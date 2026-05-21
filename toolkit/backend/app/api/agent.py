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
async def submit_human_review(run_id: str, decision: HumanReviewDecision):
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
    return {"run_id": run_id, "state": run["state"], "approved": decision.approved}


# Optional str type hint fix
from typing import Optional as Opt
