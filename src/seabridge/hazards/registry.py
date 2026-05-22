"""Hazard registry — wires all 6 hazard scorers and computes overall physical risk."""

from ..models.enums import HazardType, RiskRating
from .base import HazardResult, HazardScorer
from .scoring import compute_overall_physical_risk, rating_from_score
from .wildfire import WildfireScorer
from .inland_flood import InlandFloodScorer
from .coastal_flood import CoastalFloodScorer
from .heat_stress import HeatStressScorer
from .drought import DroughtScorer
from .wind_hurricane import WindHurricaneScorer


class HazardRegistry:
    """Runs all hazard scorers and aggregates to an overall physical risk score."""

    def __init__(self) -> None:
        self._scorers: list[HazardScorer] = [
            WildfireScorer(),
            InlandFloodScorer(),
            CoastalFloodScorer(),
            HeatStressScorer(),
            DroughtScorer(),
            WindHurricaneScorer(),
        ]

    async def score_all(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> dict[str, object]:
        """Run all hazard scorers. Returns dict with hazard results and overall score."""
        results: dict[HazardType, HazardResult] = {}
        for scorer in self._scorers:
            result = await scorer.score(lat, lon, property_data, scenario, year)
            results[scorer.hazard_type] = result

        hazard_scores = {h: r.category_score for h, r in results.items()}
        overall = compute_overall_physical_risk(hazard_scores)

        all_data_gaps: list[str] = []
        for r in results.values():
            all_data_gaps.extend(f"{r.hazard_type.value}:{gap}" for gap in r.data_gaps)

        return {
            "hazard_results": results,
            "overall_score": overall,
            "overall_rating": rating_from_score(overall),
            "data_gaps": all_data_gaps,
        }
