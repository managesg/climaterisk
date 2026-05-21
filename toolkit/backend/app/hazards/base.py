"""Base classes for hazard scoring. All scoring is deterministic and open-access only."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import math


class DataAvailability(str, Enum):
    MEASURED = "measured"
    ESTIMATED = "estimated"
    MISSING = "missing"


@dataclass
class FeatureInput:
    """A single raw feature value for hazard scoring."""
    name: str
    value: Optional[float]
    unit: str
    source_name: str
    source_url: str
    data_type: str  # observed / modeled / estimated / missing
    notes: str = ""


@dataclass
class ScoredFeature:
    name: str
    raw_value: Optional[float]
    unit: str
    normalized_score: float  # 0-100
    source_name: str
    source_url: str
    data_type: str
    notes: str = ""


def normalize(value: float, lo: float, hi: float, clip: bool = True) -> float:
    """Linear normalization to 0-100. hi = 100 (worst), lo = 0 (best)."""
    if hi == lo:
        return 0.0
    score = (value - lo) / (hi - lo) * 100
    if clip:
        score = max(0.0, min(100.0, score))
    return round(score, 1)


def normalize_inverse(value: float, lo: float, hi: float) -> float:
    """Inverse normalization — higher value = lower risk (0 score)."""
    return normalize(hi - value + lo, lo, hi)


def hazard_category_score(feature_scores: List[float]) -> float:
    """
    category_score = 0.5 * max_score + 0.5 * avg_remaining
    """
    if not feature_scores:
        return 0.0
    sorted_scores = sorted(feature_scores, reverse=True)
    max_score = sorted_scores[0]
    remaining = sorted_scores[1:]
    avg_remaining = sum(remaining) / len(remaining) if remaining else max_score
    return round(0.5 * max_score + 0.5 * avg_remaining, 1)


def fill_missing_with_median(scores: List[Optional[float]], median: float = 50.0) -> List[float]:
    """Replace None (missing data) with median score and flag as data gap."""
    return [s if s is not None else median for s in scores]


class HazardModule(ABC):
    """Abstract base for all hazard modules."""

    name: str = "unknown"
    description: str = ""

    @abstractmethod
    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        """Gather raw feature inputs. Must never call paid APIs unless explicitly enabled."""
        ...

    @abstractmethod
    def score_features(self, features: List[FeatureInput]) -> List[ScoredFeature]:
        """Normalize raw inputs to 0-100."""
        ...

    def compute(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> Dict[str, Any]:
        features = self.collect_features(lat, lon, property_attrs)
        scored = self.score_features(features)

        scores = [f.normalized_score for f in scored]
        data_gaps = [f.name for f in scored if f.data_type == "missing"]

        # Use median imputation for missing scores (conservative)
        imputed = [s for s in scores if s is not None]
        category_score = hazard_category_score(imputed) if imputed else 50.0

        from app.models.common import score_to_rating, ConfidenceLevel, confidence_from_completeness
        filled = len([f for f in scored if f.data_type != "missing"])
        confidence = confidence_from_completeness(filled, len(scored))

        top_drivers = sorted(scored, key=lambda x: x.normalized_score, reverse=True)
        top_driver_names = [f.name for f in top_drivers[:3] if f.normalized_score > 30]

        feature_score_dicts = [
            {
                "feature_name": f.name,
                "raw_value": f.raw_value,
                "raw_unit": f.unit,
                "normalized_score": f.normalized_score,
                "data_source_type": f.data_type,
                "source_name": f.source_name,
                "source_url": f.source_url,
                "notes": f.notes,
            }
            for f in scored
        ]

        return {
            "hazard": self.name,
            "applicable": True,
            "category_score": category_score,
            "rating": score_to_rating(category_score).value,
            "feature_scores": feature_score_dicts,
            "top_drivers": top_driver_names,
            "confidence": confidence.value,
            "evidence": [f.source_name for f in scored if f.data_type != "missing"],
            "data_gaps": data_gaps,
            "recommended_action": self._recommend(category_score, top_driver_names),
        }

    def _recommend(self, score: float, drivers: List[str]) -> str:
        if score > 80:
            return f"Detailed site assessment urgently required. Key drivers: {', '.join(drivers[:2])}."
        elif score > 60:
            return f"Commission specialist hazard study. Review insurance coverage. Drivers: {', '.join(drivers[:2])}."
        elif score > 40:
            return f"Monitor and include in annual review. Drivers: {', '.join(drivers[:2])}."
        return "No immediate action required. Confirm data completeness annually."
