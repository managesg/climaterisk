"""Shared enums and value types."""
from enum import Enum


class RiskRating(str, Enum):
    VERY_LOW = "Very Low"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


class TimeHorizon(str, Enum):
    CURRENT = "current"
    SHORT = "2030"
    MEDIUM = "2040"
    LONG = "2050"


class ClimateScenario(str, Enum):
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"
    SSP5_85 = "SSP5-8.5"
    NGFS_NET_ZERO = "NGFS_NET_ZERO"
    NGFS_DELAYED = "NGFS_DELAYED_TRANSITION"
    NGFS_HOT_HOUSE = "NGFS_HOTHOUSE"


class DataSourceType(str, Enum):
    OBSERVED = "observed"
    MODELED = "modeled"
    SCENARIO_ASSUMPTION = "scenario_assumption"
    AI_GENERATED = "ai_generated"
    USER_PROVIDED = "user_provided"
    MISSING = "missing"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


def score_to_rating(score: float) -> RiskRating:
    if score <= 20:
        return RiskRating.VERY_LOW
    elif score <= 40:
        return RiskRating.LOW
    elif score <= 60:
        return RiskRating.MODERATE
    elif score <= 80:
        return RiskRating.HIGH
    return RiskRating.VERY_HIGH


def confidence_from_completeness(filled: int, total: int) -> ConfidenceLevel:
    ratio = filled / total if total > 0 else 0
    if ratio >= 0.85:
        return ConfidenceLevel.HIGH
    elif ratio >= 0.65:
        return ConfidenceLevel.MEDIUM
    elif ratio >= 0.40:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.VERY_LOW
