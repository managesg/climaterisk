"""AgentRun tracks LangGraph workflow execution state."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class AgentRunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_human_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class HumanFeedback(BaseModel):
    reviewer: Optional[str] = None
    approved: bool = False
    comments: Optional[str] = None
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    corrections: Optional[Dict[str, Any]] = None


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    property_ids: List[str]
    task_type: str  # e.g. "full_assessment", "physical_only", "disclosure"
    state: AgentRunState = AgentRunState.PENDING
    workflow_steps_completed: List[str] = Field(default_factory=list)
    final_output: Optional[Dict[str, Any]] = None
    assessment_id: Optional[str] = None
    confidence: Optional[float] = None
    evidence: List[str] = Field(default_factory=list)
    approval_state: ApprovalState = ApprovalState.NOT_REQUIRED
    human_feedback: Optional[HumanFeedback] = None
    flags: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
