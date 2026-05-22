"""LangGraph state schemas for the climate risk workflow."""
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field
import operator


class WorkflowState(BaseModel):
    """Shared state passed between all workflow nodes."""
    # Inputs
    company_id: str = ""
    property_ids: List[str] = Field(default_factory=list)
    task_type: str = "full_assessment"
    scenario: str = "SSP2-4.5"
    time_horizon: str = "2050"

    # Loaded data
    company: Optional[Dict[str, Any]] = None
    properties: List[Dict[str, Any]] = Field(default_factory=list)

    # Assessment results
    physical_risk_results: List[Dict[str, Any]] = Field(default_factory=list)
    transition_risks: List[Dict[str, Any]] = Field(default_factory=list)
    nature_risks: List[Dict[str, Any]] = Field(default_factory=list)
    opportunities: List[Dict[str, Any]] = Field(default_factory=list)

    # Evidence and quality
    evidence: List[str] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: float = 0.0

    # Control flow
    requires_human_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    human_approved: bool = False
    errors: List[str] = Field(default_factory=list)

    # Output
    disclosure_summary: Optional[Dict[str, Any]] = None
    run_id: str = ""
    steps_completed: List[str] = Field(default_factory=list)

    def record_step(self, step: str) -> "WorkflowState":
        self.steps_completed.append(step)
        return self
