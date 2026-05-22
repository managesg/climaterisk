from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    company_id: str
    property_ids: list[str]
    task_type: str  # "full_assessment" | "transition_risk" | "disclosure"

    # Loaded entities
    company: Optional[dict[str, Any]]
    properties: Optional[list[dict[str, Any]]]
    enriched_properties: Optional[list[dict[str, Any]]]

    # Scenario parameters
    scenario: str   # ssp126 | ssp245 | ssp585
    year: int       # 2030 | 2050 | 2100

    # Results
    hazard_data: Optional[dict[str, Any]]
    physical_risk_results: Optional[dict[str, Any]]   # assessment_id → HazardResult dict
    transition_risk: Optional[dict[str, Any]]
    opportunities: Optional[dict[str, Any]]
    nature_risk: Optional[dict[str, Any]]
    disclosure_draft: Optional[str]

    # Quality control
    confidence: float
    evidence: list[dict[str, Any]]
    data_gaps: list[str]
    assumptions: list[str]
    human_review_required: bool
    human_feedback: Optional[str]

    # Errors
    errors: list[str]
