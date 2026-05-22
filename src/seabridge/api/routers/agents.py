"""Agent run endpoints — LangGraph workflow."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...agents.workflow import run_assessment as run_agent_assessment
from ...models.agent_run import AgentRun
from ...models.enums import ApprovalState

router = APIRouter()


class AgentRunRequest(BaseModel):
    company_id: str
    property_ids: list[str]
    scenario: str = "ssp245"
    year: int = 2050
    task_type: str = "full_assessment"


class HumanFeedback(BaseModel):
    feedback: str
    approved: bool


@router.post("/run", status_code=202)
async def start_agent_run(body: AgentRunRequest) -> dict:
    """Start a full LangGraph workflow assessment. Returns run_id."""
    final_state = await run_agent_assessment(
        company_id=body.company_id,
        property_ids=body.property_ids,
        scenario=body.scenario,
        year=body.year,
        task_type=body.task_type,
    )
    return {
        "run_id": final_state.get("run_id"),
        "status": "complete" if not final_state.get("human_review_required") else "pending_review",
        "confidence": final_state.get("confidence"),
        "data_gaps_count": len(final_state.get("data_gaps", [])),
        "physical_risk_results": final_state.get("physical_risk_results"),
        "transition_risk": final_state.get("transition_risk"),
        "opportunities": final_state.get("opportunities"),
        "nature_risk": final_state.get("nature_risk"),
        "disclosure_draft": final_state.get("disclosure_draft"),
        "errors": final_state.get("errors", []),
    }


@router.get("/{run_id}")
async def get_agent_run(run_id: str) -> dict:
    run = await AgentRun.find_one({"run_id": uuid.UUID(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run.model_dump(mode="json")


@router.post("/{run_id}/feedback")
async def submit_human_feedback(run_id: str, body: HumanFeedback) -> dict:
    """Submit human review decision for a pending agent run."""
    run = await AgentRun.find_one({"run_id": uuid.UUID(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    run.human_feedback = body.feedback
    run.approval_state = ApprovalState.APPROVED if body.approved else ApprovalState.REJECTED
    await run.save()
    return {"run_id": run_id, "approval_state": run.approval_state.value}
