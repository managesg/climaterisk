"""Portfolio-level physical risk scorer — aggregates across hazards."""
from typing import Dict, Any, List, Optional
import logging
from .wildfire import WildfireHazard
from .inland_flood import InlandFloodHazard
from .coastal_flood import CoastalFloodHazard
from .heat_stress import HeatStressHazard
from .drought import DroughtHazard
from .wind import WindHazard
from app.models.common import score_to_rating, ConfidenceLevel, confidence_from_completeness

logger = logging.getLogger(__name__)

ALL_HAZARDS = [
    WildfireHazard(),
    InlandFloodHazard(),
    CoastalFloodHazard(),
    HeatStressHazard(),
    DroughtHazard(),
    WindHazard(),
]


def _is_coastal_applicable(lat: float, lon: float, props: Dict[str, Any]) -> bool:
    dist = props.get("distance_to_coast_km")
    return dist is None or dist < 50


def score_property(
    lat: float,
    lon: float,
    property_attrs: Dict[str, Any],
    scenario: str = "SSP2-4.5",
    time_horizon: str = "2050",
) -> Dict[str, Any]:
    """
    Score all hazards for a single property.
    Returns overall score, rating, per-hazard results, and metadata.
    """
    hazard_results = []

    for hazard in ALL_HAZARDS:
        try:
            if hazard.name == "Coastal Flood / Sea Level Rise":
                if not _is_coastal_applicable(lat, lon, property_attrs):
                    hazard_results.append({
                        "hazard": hazard.name,
                        "applicable": False,
                        "category_score": 0.0,
                        "rating": "Very Low",
                        "feature_scores": [],
                        "top_drivers": [],
                        "confidence": "high",
                        "evidence": ["distance_to_coast > 50 km"],
                        "data_gaps": [],
                        "recommended_action": "Not applicable — inland location.",
                        "scenario": scenario,
                        "time_horizon": time_horizon,
                    })
                    continue

            result = hazard.compute(lat, lon, property_attrs)
            result["scenario"] = scenario
            result["time_horizon"] = time_horizon
            hazard_results.append(result)
        except Exception as e:
            logger.error("Hazard %s failed for lat=%s lon=%s: %s", hazard.name, lat, lon, e)
            hazard_results.append({
                "hazard": hazard.name,
                "applicable": True,
                "category_score": 50.0,
                "rating": "Moderate",
                "feature_scores": [],
                "top_drivers": [],
                "confidence": "very_low",
                "evidence": [],
                "data_gaps": [f"Scoring error: {str(e)}"],
                "recommended_action": "Manual review required due to scoring error.",
                "scenario": scenario,
                "time_horizon": time_horizon,
            })

    applicable = [r for r in hazard_results if r.get("applicable", True)]
    overall_score = _overall_score(applicable)
    overall_rating = score_to_rating(overall_score)

    all_gaps = []
    for r in hazard_results:
        all_gaps.extend(r.get("data_gaps", []))

    sorted_by_score = sorted(applicable, key=lambda x: x["category_score"], reverse=True)
    top_hazards = [r["hazard"] for r in sorted_by_score[:3] if r["category_score"] > 30]

    confidences = [r.get("confidence", "low") for r in applicable]
    overall_conf = _aggregate_confidence(confidences)

    return {
        "overall_score": round(overall_score, 1),
        "overall_rating": overall_rating.value,
        "hazard_results": hazard_results,
        "top_hazards": top_hazards,
        "confidence": overall_conf,
        "data_gaps": list(set(all_gaps)),
        "scenario": scenario,
        "time_horizon": time_horizon,
        "methodology_note": (
            "Open-access screening tier only. Scores are indicative. "
            "Replace coarse proxies with site-specific data for disclosure use."
        ),
    }


def score_portfolio(
    properties: List[Dict[str, Any]],
    scenario: str = "SSP2-4.5",
    time_horizon: str = "2050",
) -> Dict[str, Any]:
    """Score a list of properties and aggregate portfolio-level results."""
    results = []
    for prop in properties:
        lat = prop.get("latitude", 0)
        lon = prop.get("longitude", 0)
        result = score_property(lat, lon, prop, scenario, time_horizon)
        result["property_id"] = prop.get("property_id", "")
        result["property_name"] = prop.get("name", "")
        results.append(result)

    if not results:
        return {"properties": [], "portfolio_summary": {}}

    scores = [r["overall_score"] for r in results]
    high_risk = [r for r in results if r["overall_score"] > 60]

    return {
        "properties": results,
        "portfolio_summary": {
            "property_count": len(results),
            "average_score": round(sum(scores) / len(scores), 1),
            "max_score": round(max(scores), 1),
            "high_risk_count": len(high_risk),
            "high_risk_property_ids": [r["property_id"] for r in high_risk],
        },
    }


def _overall_score(applicable: List[Dict]) -> float:
    if not applicable:
        return 0.0
    scores = [r["category_score"] for r in applicable]
    scores_sorted = sorted(scores, reverse=True)
    if len(scores_sorted) == 1:
        return scores_sorted[0]
    # Weight highest material hazard twice — denominator is n+1
    weighted = [scores_sorted[0] * 2] + scores_sorted[1:]
    return sum(weighted) / (len(scores_sorted) + 1)


def _aggregate_confidence(confidences: List[str]) -> str:
    order = {"high": 3, "medium": 2, "low": 1, "very_low": 0}
    if not confidences:
        return "low"
    min_conf = min(order.get(c, 0) for c in confidences)
    reverse = {v: k for k, v in order.items()}
    return reverse[min_conf]
