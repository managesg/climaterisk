from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field

from .enums import ApprovalState
from .assessment import EvidenceItem


class AgentRun(Document):
    run_id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    property_ids: list[UUID]
    task_type: str  # e.g. "full_assessment", "transition_risk", "disclosure"

    state: dict[str, Any] = Field(default_factory=dict)  # LangGraph state snapshot
    final_output: Optional[dict[str, Any]] = None

    confidence: Optional[float] = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)

    approval_state: ApprovalState = ApprovalState.NOT_REQUIRED
    human_feedback: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_runs"
