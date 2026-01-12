"""Pydantic schemas for The Hive API."""

from uuid import UUID
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkflowSubmission(BaseModel):
    """Schema for workflow submission."""

    input_request: str = Field(..., description="Feature request in natural language")
    project_context_id: Optional[str] = Field(None, description="Optional project context")
    priority: str = Field("MEDIUM", description="Workflow priority")


class WorkflowSubmissionResponse(BaseModel):
    """Schema for workflow submission response."""

    workflow_id: str
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class WorkflowStatus(BaseModel):
    """Schema for workflow status."""

    workflow_id: str
    status: str
    current_stage: Optional[str] = None
    progress: dict[str, Any] = Field(default_factory=dict)
    agent_states: list[dict] = Field(default_factory=list)
    estimated_remaining_seconds: Optional[int] = None


class ArtifactSummary(BaseModel):
    """Schema for artifact summary."""

    artifact_id: str
    artifact_type: str
    stage: str
    created_at: datetime
    approval_status: str
