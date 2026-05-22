"""Disclosure generation endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...agents.workflow import run_assessment as run_agent_assessment
from ...disclosure.generator import DisclosureGenerator
from ...models.agent_run import AgentRun

router = APIRouter()


class DisclosureRequest(BaseModel):
    company_id: str
    property_ids: list[str]
    scenario: str = "ssp245"
    year: int = 2050


@router.post("/generate")
async def generate_disclosure(body: DisclosureRequest) -> dict:
    """Run a full assessment and generate an ISSB/TCFD/TNFD disclosure report."""
    final_state = await run_agent_assessment(
        company_id=body.company_id,
        property_ids=body.property_ids,
        scenario=body.scenario,
        year=body.year,
        task_type="disclosure",
    )
    disclosure = final_state.get("disclosure_draft") or ""
    return {
        "run_id": final_state.get("run_id"),
        "disclosure_markdown": disclosure,
        "confidence": final_state.get("confidence"),
        "data_gaps": final_state.get("data_gaps", []),
        "human_review_required": final_state.get("human_review_required", False),
    }


@router.get("/{run_id}")
async def get_disclosure(run_id: str) -> dict:
    """Retrieve disclosure from a completed agent run."""
    run = await AgentRun.find_one({"run_id": uuid.UUID(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    output = run.final_output or {}
    gen = DisclosureGenerator()
    draft = gen.generate({
        "company": {},
        "physical_risk_results": output.get("physical_risk"),
        "transition_risk": output.get("transition_risk"),
        "opportunities": output.get("opportunities"),
        "nature_risk": output.get("nature_risk"),
        "data_gaps": output.get("data_gaps", []),
        "confidence": run.confidence or 0.0,
        "scenario": "ssp245",
        "year": 2050,
        "assumptions": [],
    })
    return {
        "run_id": run_id,
        "disclosure_markdown": draft,
        "approval_state": run.approval_state.value,
    }
