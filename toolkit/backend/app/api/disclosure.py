"""Disclosure report generation endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.data.store import get_agent_run, list_assessments, get_company
from app.disclosure.generator import DisclosureGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


class DisclosureRequest(BaseModel):
    run_id: Optional[str] = None
    company_id: Optional[str] = None
    scenario: str = "SSP2-4.5"
    time_horizon: str = "2050"


@router.post("/generate")
async def generate_disclosure(request: DisclosureRequest):
    if request.run_id:
        run = await get_agent_run(request.run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {request.run_id} not found")
        if run.get("final_output"):
            return {
                "source": "agent_run",
                "run_id": request.run_id,
                "disclosure": run["final_output"],
            }

    if request.company_id:
        company = await get_company(request.company_id)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company {request.company_id} not found")
        assessments = await list_assessments(company_id=request.company_id)
        if not assessments:
            raise HTTPException(
                status_code=422,
                detail="No assessments found for this company. Run a risk assessment first."
            )
        gen = DisclosureGenerator()
        physical_results = [a.get("physical_risk", {}) for a in assessments if a.get("physical_risk")]
        disclosure = gen.generate(
            company=company,
            properties=[],
            physical_risk_results=physical_results,
            transition_risks=[],
            nature_risks=[],
            opportunities=[],
            scenario=request.scenario,
            time_horizon=request.time_horizon,
            confidence=0.5,
            data_gaps=["Full workflow not run — using saved assessments only"],
            assumptions=[],
        )
        return {"source": "assessments", "disclosure": disclosure}

    raise HTTPException(status_code=400, detail="Provide run_id or company_id")


@router.get("/run/{run_id}")
async def get_disclosure_from_run(run_id: str):
    run = await get_agent_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    output = run.get("final_output")
    if not output:
        return {"run_id": run_id, "state": run.get("state"), "disclosure": None,
                "message": "Disclosure not yet generated. Check run state."}
    return {"run_id": run_id, "state": run.get("state"), "disclosure": output}
