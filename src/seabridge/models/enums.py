from enum import Enum


class HazardType(str, Enum):
    WILDFIRE = "wildfire"
    INLAND_FLOOD = "inland_flood"
    COASTAL_FLOOD = "coastal_flood"
    HEAT_STRESS = "heat_stress"
    DROUGHT = "drought"
    WIND_HURRICANE = "wind_hurricane"


class RiskRating(str, Enum):
    VERY_LOW = "very_low"    # 0-20
    LOW = "low"              # 21-40
    MODERATE = "moderate"    # 41-60
    HIGH = "high"            # 61-80
    VERY_HIGH = "very_high"  # 81-100


class DataType(str, Enum):
    OBSERVED = "observed"
    MODELED = "modeled"
    SCENARIO = "scenario"
    AI_GENERATED = "ai_generated"
    USER_PROVIDED = "user_provided"
    MISSING = "missing"


class Scenario(str, Enum):
    SSP1_26 = "ssp126"
    SSP2_45 = "ssp245"
    SSP5_85 = "ssp585"


class ApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
