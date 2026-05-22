"""Risk assessment result model — physical, transition, nature."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.common import (
    RiskRating, TimeHorizon, ClimateScenario, DataSourceType, ConfidenceLevel
)
import uuid


class FeatureScore(BaseModel):
    """A single indicator/feature within a hazard assessment."""
    feature_name: str
    raw_value: Optional[float] = None
    raw_unit: Optional[str] = None
    normalized_score: float = Field(..., ge=0, le=100)
    data_source_type: DataSourceType
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None


class HazardResult(BaseModel):
    """Scored result for one hazard."""
    hazard: str
    applicable: bool = True
    category_score: float = Field(..., ge=0, le=100)
    rating: RiskRating
    feature_scores: List[FeatureScore]
    top_drivers: List[str]
    confidence: ConfidenceLevel
    evidence: List[str]
    data_gaps: List[str]
    recommended_action: str
    scenario: ClimateScenario
    time_horizon: TimeHorizon


class PhysicalRiskSummary(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    overall_rating: RiskRating
    hazard_results: List[HazardResult]
    top_hazards: List[str]
    confidence: ConfidenceLevel
    data_gaps: List[str]
    methodology_note: str = (
        "Scores reflect open-access screening only. "
        "Not a substitute for engineering-grade catastrophe modelling."
    )


class TransitionRiskItem(BaseModel):
    category: str
    risk_driver: str
    description: str
    severity: RiskRating
    time_horizon: TimeHorizon
    confidence: ConfidenceLevel
    scenario: ClimateScenario
    financial_impact_note: str
    required_data: List[str]
    tcfd_disclosure_area: str
    evidence: List[str]
    data_source_type: DataSourceType = DataSourceType.AI_GENERATED


class NatureRiskItem(BaseModel):
    category: str
    dependency_or_impact: str
    description: str
    severity: RiskRating
    time_horizon: TimeHorizon
    confidence: ConfidenceLevel
    evidence: List[str]
    data_gaps: List[str]
    tnfd_leap_step: str
    data_source_type: DataSourceType = DataSourceType.AI_GENERATED


class OpportunityItem(BaseModel):
    title: str
    category: str
    description: str
    linked_risks: List[str]
    required_data: List[str]
    implementation_actions: List[str]
    expected_benefit_type: str
    financial_estimate_note: str
    evidence: List[str]
    confidence: ConfidenceLevel
    time_horizon: TimeHorizon
    disclosure_relevance: str
    data_source_type: DataSourceType = DataSourceType.AI_GENERATED


class RiskAssessment(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    company_id: str
    scenario: ClimateScenario
    time_horizon: TimeHorizon
    physical_risk: Optional[PhysicalRiskSummary] = None
    transition_risks: Optional[List[TransitionRiskItem]] = None
    nature_risks: Optional[List[NatureRiskItem]] = None
    opportunities: Optional[List[OpportunityItem]] = None
    overall_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    data_gaps: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
