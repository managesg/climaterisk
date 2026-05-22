from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from ..models.enums import DataType, HazardType, RiskRating


@dataclass
class FeatureScore:
    feature_name: str
    raw_value: Optional[float]
    normalized_score: float          # 0-100
    source: str
    data_type: DataType
    is_available: bool = True
    confidence: float = 1.0
    source_url: Optional[str] = None
    note: Optional[str] = None


@dataclass
class HazardResult:
    hazard_type: HazardType
    feature_scores: list[FeatureScore] = field(default_factory=list)
    category_score: float = 0.0
    rating: RiskRating = RiskRating.VERY_LOW
    confidence: float = 0.0
    top_drivers: list[str] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)
    recommended_action: Optional[str] = None


class HazardScorer(ABC):
    hazard_type: HazardType

    @abstractmethod
    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        """Score this hazard for a given location, scenario, and year."""

    @staticmethod
    def normalize(value: float, low: float, high: float) -> float:
        """Linearly map value from [low, high] to [0, 100], clamped."""
        if high <= low:
            return 0.0
        return float(max(0.0, min(100.0, (value - low) / (high - low) * 100.0)))
