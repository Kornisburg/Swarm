"""Workflow state management for The Hive."""

from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    """State for LangGraph workflow execution."""

    # Input
    input_request: str = Field(..., description="User's feature request")

    # Workflow tracking
    workflow_id: Optional[str] = Field(None, description="Workflow session ID")
    status: str = Field("PENDING", description="Current workflow status")
    current_stage: Optional[str] = Field(None, description="Current workflow stage")

    # Artifacts generated during workflow
    artifacts: dict[str, Any] = Field(default_factory=dict, description="Generated artifacts")
    spec_artifact: Optional[dict] = Field(None, description="Specification artifact")
    design_artifact: Optional[dict] = Field(None, description="Design artifact")
    code_artifact: Optional[dict] = Field(None, description="Code artifact")

    # Decisions made during workflow
    decisions: list[dict] = Field(default_factory=list, description="Agent decisions")

    # Progress tracking
    stage_history: list[str] = Field(default_factory=list, description="Completed stages")
    error_message: Optional[str] = Field(None, description="Error details if failed")

    # Performance metrics
    tokens_used: int = Field(0, description="Total tokens consumed")
    cost_estimate: float = Field(0.0, description="Estimated cost in USD")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
