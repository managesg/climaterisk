from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID, uuid4
from beanie import Document
from pydantic import BaseModel, Field

from .enums import HazardType, RiskRating, DataType, Scenario


class EvidenceItem(BaseModel):
    claim: str
    source: str
    source_url: Optional[str] = None
    scenario: Optional[str] = None
    time_horizon: Optional[int] = None
    confidence: float = 0.0
    data_type: DataType = DataType.MISSING
    accessed_at: Optional[datetime] = None


class FeatureScoreRecord(BaseModel):
    feature_name: str
    raw_value: Optional[Union[float, str]] = None
    normalized_score: float          # 0-100
    source: str
    source_url: Optional[str] = None
    data_type: DataType
    is_available: bool = True
    confidence: float = 1.0
    note: Optional[str] = None


class HazardScore(BaseModel):
    hazard: HazardType
    feature_scores: list[FeatureScoreRecord]
    category_score: float            # 0-100, formula: 0.5*max + 0.5*avg_remaining
    rating: RiskRating
    confidence: float                # weighted average of feature confidences
    top_drivers: list[str]           # top 3 feature names by normalized_score
    data_gaps: list[str]             # features where is_available=False
    recommended_action: Optional[str] = None


class RiskAssessment(Document):
    assessment_id: UUID = Field(default_factory=uuid4)
    property_id: UUID
    company_id: UUID

    scenario: Scenario
    time_horizon: int                # year: 2030, 2050, or 2100

    hazard_scores: dict[str, HazardScore] = Field(default_factory=dict)
    overall_score: Optional[float] = None   # 0-100
    overall_rating: Optional[RiskRating] = None

    confidence: float = 0.0
    evidence: list[EvidenceItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "risk_assessments"
