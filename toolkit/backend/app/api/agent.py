"""AI agent workflow endpoints."""
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.data.store import (
    save_agent_run, get_agent_run, list_agent_runs,
    get_all_companies_dict, get_all_properties_dict,
)
from app.models.agent_run import AgentRun, AgentRunState, ApprovalState, HumanFeedback

logger = logging.getLogger(__name__)
router = APIRouter()


class AssessmentRequest(BaseModel):
    company_id: str
    property_ids: List[str]
    task_type: str = "full_assessment"
    scenario: str = "SSP2-4.5"
    time_horizon: str = "2050"


class HumanReviewDecision(BaseModel):
    run_id: str
    approved: bool
    reviewer: Optional[str] = None
    comments: Optional[str] = None


async def _run_workflow_background(run_id: str, request: AssessmentRequest):
    """Execute the full LangGraph assessment workflow in background."""
    try:
        run_data = await get_agent_run(run_id)
        if run_data:
            run_data["state"] = AgentRunState.RUNNING.value
            run_data["updated_at"] = datetime.utcnow().isoformat()
            await save_agent_run(run_data)

        from app.agents.workflow import run_assessment
        result_state = await run_assessment(
            company_id=request.company_id,
            property_ids=request.property_ids,
            task_type=request.task_type,
            scenario=request.scenario,
            time_horizon=request.time_horizon,
            run_id=run_id,
            in_memory_companies=get_all_companies_dict(),
            in_memory_properties=get_all_properties_dict(),
        )

        run_data = await get_agent_run(run_id)
        if run_data:
            if result_state.requires_human_review:
                run_data["state"] = AgentRunState.AWAITING_REVIEW.value
                run_data["approval_state"] = ApprovalState.PENDING.value
                run_data["flags"] = result_state.review_reasons
            else:
                run_data["state"] = AgentRunState.COMPLETED.value
                run_data["approval_state"] = ApprovalState.AUTO_APPROVED.value

            run_data["final_output"] = result_state.disclosure_summary
            run_data["confidence"] = result_state.confidence
            run_data["evidence"] = result_state.evidence
            run_data["workflow_steps_completed"] = result_state.steps_completed
            run_data["scenario"] = request.scenario
            run_data["time_horizon"] = request.time_horizon
            run_data["physical_risk_results"] = result_state.physical_risk_results
            run_data["transition_risks"] = result_state.transition_risks
            run_data["nature_risks"] = result_state.nature_risks
            run_data["opportunities"] = result_state.opportunities
            run_data["data_gaps"] = result_state.data_gaps
            run_data["assumptions"] = result_state.assumptions
            run_data["updated_at"] = datetime.utcnow().isoformat()
            await save_agent_run(run_data)

    except Exception as e:
        logger.error("Workflow failed for run %s: %s", run_id, e, exc_info=True)
        run_data = await get_agent_run(run_id)
        if run_data:
            run_data["state"] = AgentRunState.FAILED.value
            run_data["error"] = str(e)
            run_data["updated_at"] = datetime.utcnow().isoformat()
            await save_agent_run(run_data)


@router.post("/run")
async def start_assessment(request: AssessmentRequest, background_tasks: BackgroundTasks):
    run = AgentRun(
        company_id=request.company_id,
        property_ids=request.property_ids,
        task_type=request.task_type,
        state=AgentRunState.PENDING,
    )
    await save_agent_run(run.model_dump())
    background_tasks.add_task(_run_workflow_background, run.run_id, request)
    return {"run_id": run.run_id, "state": run.state, "message": "Assessment started"}


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    run = await get_agent_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.get("/runs")
async def list_runs(company_id: Optional[str] = None):
    runs = await list_agent_runs(company_id=company_id)
    return {"runs": runs, "count": len(runs)}


@router.post("/run/{run_id}/review")
async def submit_human_review(run_id: str, decision: HumanReviewDecision, background_tasks: BackgroundTasks):
    run = await get_agent_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    if run["state"] != AgentRunState.AWAITING_REVIEW.value:
        raise HTTPException(status_code=400, detail=f"Run is not awaiting review (state: {run['state']})")

    run["human_feedback"] = HumanFeedback(
        reviewer=decision.reviewer,
        approved=decision.approved,
        comments=decision.comments,
    ).model_dump()
    run["approval_state"] = ApprovalState.APPROVED.value if decision.approved else ApprovalState.REJECTED.value
    run["state"] = AgentRunState.COMPLETED.value if decision.approved else AgentRunState.FAILED.value
    run["updated_at"] = datetime.utcnow().isoformat()
    await save_agent_run(run)

    if decision.approved:
        background_tasks.add_task(_generate_disclosure_after_review, run_id)

    return {"run_id": run_id, "state": run["state"], "approved": decision.approved}


async def _generate_disclosure_after_review(run_id: str):
    """Generate disclosure summary after human review approval."""
    try:
        from app.agents.nodes import generate_disclosure_summary
        from app.agents.states import WorkflowState
        run = await get_agent_run(run_id)
        if not run:
            return
        # Reconstruct enough state to generate disclosure
        companies = get_all_companies_dict()
        properties = get_all_properties_dict()
        company = companies.get(run.get("company_id", ""), {})
        props = [properties.get(pid, {}) for pid in run.get("property_ids", []) if pid in properties]
        state = WorkflowState(
            company_id=run.get("company_id", ""),
            property_ids=run.get("property_ids", []),
            company=company,
            properties=props,
            physical_risk_results=run.get("physical_risk_results", []),
            transition_risks=run.get("transition_risks", []),
            nature_risks=run.get("nature_risks", {}),
            opportunities=run.get("opportunities", []),
            scenario=run.get("scenario", "SSP2-4.5"),
            time_horizon=run.get("time_horizon", "2050"),
            confidence=run.get("confidence", 0.0),
            data_gaps=run.get("data_gaps", []),
            assumptions=run.get("assumptions", []),
            steps_completed=run.get("workflow_steps_completed", []),
            evidence=run.get("evidence", []),
        )
        result = await generate_disclosure_summary(state)
        run["final_output"] = result.get("disclosure_summary")
        run["workflow_steps_completed"] = result.get("steps_completed", state.steps_completed)
        run["updated_at"] = datetime.utcnow().isoformat()
        await save_agent_run(run)
    except Exception as e:
        logger.error("Disclosure generation after review failed for run %s: %s", run_id, e, exc_info=True)


# Optional str type hint fix
from typing import Optional as Opt
