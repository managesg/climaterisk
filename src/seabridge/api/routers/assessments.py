"""Assessment endpoints — run physical risk scoring."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...hazards.registry import HazardRegistry
from ...models.assessment import EvidenceItem, FeatureScoreRecord, HazardScore, RiskAssessment
from ...models.enums import DataType, Scenario
from ...models.property import Property

router = APIRouter()
_registry = HazardRegistry()


class AssessmentRunRequest(BaseModel):
    property_ids: list[str]
    company_id: str
    scenario: str = "ssp245"
    time_horizon: int = 2050


@router.post("/run", status_code=201)
async def run_assessment(body: AssessmentRunRequest) -> dict:
    """Run physical risk scoring for one or more properties."""
    results = []
    for pid in body.property_ids:
        prop = await Property.find_one({"property_id": uuid.UUID(pid)})
        if not prop:
            raise HTTPException(status_code=404, detail=f"Property {pid} not found")

        prop_dict = prop.model_dump(mode="json")
        scored = await _registry.score_all(
            prop.latitude,
            prop.longitude,
            prop_dict,
            body.scenario,
            body.time_horizon,
        )
        hazard_results = scored["hazard_results"]
        hazard_scores_doc: dict[str, HazardScore] = {}

        for htype, hr in hazard_results.items():
            feature_records = [
                FeatureScoreRecord(
                    feature_name=f.feature_name,
                    raw_value=f.raw_value if isinstance(f.raw_value, (int, float, str, type(None))) else str(f.raw_value),
                    normalized_score=f.normalized_score,
                    source=f.source,
                    source_url=f.source_url,
                    data_type=f.data_type,
                    is_available=f.is_available,
                    confidence=f.confidence,
                    note=f.note,
                )
                for f in hr.feature_scores
            ]
            hazard_scores_doc[htype.value] = HazardScore(
                hazard=htype,
                feature_scores=feature_records,
                category_score=hr.category_score,
                rating=hr.rating,
                confidence=hr.confidence,
                top_drivers=hr.top_drivers,
                data_gaps=hr.data_gaps,
                recommended_action=hr.recommended_action,
            )

        avg_confidence = (
            sum(hs.confidence for hs in hazard_scores_doc.values()) / max(len(hazard_scores_doc), 1)
        )

        assessment = RiskAssessment(
            property_id=uuid.UUID(pid),
            company_id=uuid.UUID(body.company_id),
            scenario=Scenario(body.scenario),
            time_horizon=body.time_horizon,
            hazard_scores=hazard_scores_doc,
            overall_score=scored["overall_score"],
            overall_rating=scored["overall_rating"],
            confidence=avg_confidence,
            data_gaps=scored["data_gaps"],
            assumptions=[
                "Feature normalization bounds calibrated to representative US building stock.",
                "Stub providers return zero scores; all data gaps are listed explicitly.",
                f"Scenario: {body.scenario}, time horizon: {body.time_horizon}.",
            ],
        )
        await assessment.insert()
        results.append(assessment.model_dump(mode="json"))

    return {"assessments": results, "count": len(results)}


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str) -> dict:
    assessment = await RiskAssessment.find_one({"assessment_id": uuid.UUID(assessment_id)})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment.model_dump(mode="json")


@router.get("")
async def list_assessments(
    property_id: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[dict]:
    query: dict = {}
    if property_id:
        query["property_id"] = uuid.UUID(property_id)
    if company_id:
        query["company_id"] = uuid.UUID(company_id)
    assessments = await RiskAssessment.find(query).to_list()
    return [a.model_dump(mode="json") for a in assessments]
