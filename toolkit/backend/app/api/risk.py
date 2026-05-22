"""Physical risk scoring endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.hazards.scorer import score_property, score_portfolio
from app.data.store import get_property, list_properties, save_assessment
from app.models.common import ClimateScenario, TimeHorizon
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class SinglePropertyRiskRequest(BaseModel):
    property_id: str
    scenario: ClimateScenario = ClimateScenario.SSP2_45
    time_horizon: TimeHorizon = TimeHorizon.LONG


class PortfolioRiskRequest(BaseModel):
    company_id: str
    scenario: ClimateScenario = ClimateScenario.SSP2_45
    time_horizon: TimeHorizon = TimeHorizon.LONG
    property_ids: Optional[List[str]] = None


@router.post("/property")
async def score_single_property(request: SinglePropertyRiskRequest):
    prop = await get_property(request.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {request.property_id} not found")

    result = score_property(
        lat=prop["latitude"],
        lon=prop["longitude"],
        property_attrs=prop,
        scenario=request.scenario.value,
        time_horizon=request.time_horizon.value,
    )
    result["property_id"] = prop["property_id"]
    result["property_name"] = prop.get("name", "")

    assessment = {
        "assessment_id": str(uuid.uuid4()),
        "property_id": request.property_id,
        "company_id": prop.get("company_id", ""),
        "scenario": request.scenario.value,
        "time_horizon": request.time_horizon.value,
        "physical_risk": result,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    await save_assessment(assessment)
    return {"assessment": assessment, "physical_risk": result}


@router.post("/portfolio")
async def score_company_portfolio(request: PortfolioRiskRequest):
    if request.property_ids:
        props = []
        for pid in request.property_ids:
            p = await get_property(pid)
            if p:
                props.append(p)
    else:
        props = await list_properties(company_id=request.company_id)

    if not props:
        raise HTTPException(status_code=404, detail="No properties found")

    result = score_portfolio(
        properties=props,
        scenario=request.scenario.value,
        time_horizon=request.time_horizon.value,
    )
    return result


@router.get("/property/{property_id}/quick")
async def quick_screen(
    property_id: str,
    scenario: ClimateScenario = ClimateScenario.SSP2_45,
    time_horizon: TimeHorizon = TimeHorizon.LONG,
):
    prop = await get_property(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    result = score_property(
        lat=prop["latitude"],
        lon=prop["longitude"],
        property_attrs=prop,
        scenario=scenario.value,
        time_horizon=time_horizon.value,
    )
    return {
        "property_id": property_id,
        "overall_score": result["overall_score"],
        "overall_rating": result["overall_rating"],
        "top_hazards": result["top_hazards"],
        "confidence": result["confidence"],
        "scenario": scenario.value,
        "time_horizon": time_horizon.value,
        "data_gaps": result.get("data_gaps", [])[:5],
    }
