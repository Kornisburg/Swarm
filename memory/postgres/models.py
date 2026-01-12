"""SQLAlchemy models for The Hive."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Float,
    Integer,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStage(str, Enum):
    """Workflow execution stages."""

    SPEC = "spec"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    DEPLOY = "deploy"


class ArtifactType(str, Enum):
    """Artifact types."""

    SPECIFICATION = "SPECIFICATION"
    DESIGN = "DESIGN"
    CODE = "CODE"
    REVIEW = "REVIEW"
    TEST_SUITE = "TEST_SUITE"


class ApprovalStatus(str, Enum):
    """Artifact approval status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AgentType(str, Enum):
    """Agent types."""

    SPEC_AGENT = "SPEC_AGENT"
    DESIGN_AGENT = "DESIGN_AGENT"
    IMPLEMENTATION_AGENT = "IMPLEMENTATION_AGENT"
    REVIEW_AGENT = "REVIEW_AGENT"
    TEST_AGENT = "TEST_AGENT"
    DEPLOYMENT_AGENT = "DEPLOYMENT_AGENT"


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"


class SandboxStatus(str, Enum):
    """Sandbox execution status."""

    CREATING = "CREATING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


class WorkflowSession(Base):
    """Workflow execution session."""

    __tablename__ = "workflow_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_context_id = Column(UUID(as_uuid=True), ForeignKey("project_contexts.id"), nullable=True)
    status = Column(String(50), nullable=False, default=WorkflowStatus.PENDING.value)
    input_request = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    current_stage = Column(String(50), nullable=True)
    artifacts_summary = Column(JSONB, nullable=True)
    performance_metrics = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project_context = relationship("ProjectContext", back_populates="workflows")
    decisions = relationship("DecisionRecord", back_populates="workflow")
    artifacts = relationship("Artifact", back_populates="workflow")
    agent_states = relationship("AgentState", back_populates="workflow")
    sandbox_sessions = relationship("SandboxSession", back_populates="workflow")

    __table_args__ = (
        Index("idx_workflow_sessions_status", "status"),
        Index("idx_workflow_sessions_created", "created_at"),
        Index("idx_workflow_sessions_project", "project_context_id"),
    )


class ProjectContext(Base):
    """Project context for multi-session workflows."""

    __tablename__ = "project_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(255), unique=True, nullable=False)
    project_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    codebase_index_id = Column(String(255), nullable=True)
    knowledge_base_id = Column(String(255), nullable=True)

    # Relationships
    workflows = relationship("WorkflowSession", back_populates="project_context")


class DecisionRecord(Base):
    """Agent decision record for provenance tracking."""

    __tablename__ = "decision_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_sessions.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    decision_type = Column(String(100), nullable=False)
    input_context = Column(JSONB, nullable=False)
    output_decision = Column(JSONB, nullable=False)
    confidence = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    dependencies = Column(JSONB, nullable=True)
    vector_embedding_id = Column(String(255), nullable=True)

    # Relationships
    workflow = relationship("WorkflowSession", back_populates="decisions")

    __table_args__ = (
        Index("idx_decision_records_workflow", "workflow_id"),
        Index("idx_decision_records_agent", "agent_type"),
        Index("idx_decision_records_timestamp", "timestamp"),
    )


class Artifact(Base):
    """Generated artifacts from workflow execution."""

    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_sessions.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    stage = Column(String(50), nullable=False)
    content = Column(JSONB, nullable=False)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approval_status = Column(String(50), default=ApprovalStatus.PENDING.value, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    workflow = relationship("WorkflowSession", back_populates="artifacts")

    __table_args__ = (Index("idx_artifacts_workflow", "workflow_id"),)


class AgentState(Base):
    """Current state of an agent during workflow execution."""

    __tablename__ = "agent_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_sessions.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    current_task = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_bytes = Column(Integer, nullable=True)
    tokens_consumed = Column(Integer, default=0, nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("WorkflowSession", back_populates="agent_states")

    __table_args__ = (
        Index("idx_agent_states_workflow", "workflow_id"),
        Index("idx_agent_states_status", "status"),
    )


class SandboxSession(Base):
    """Sandbox execution session for code execution."""

    __tablename__ = "sandbox_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_sessions.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=True)
    container_id = Column(String(255), nullable=True)
    image_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    resource_limits = Column(JSONB, nullable=False)
    resource_usage = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)

    # Relationships
    workflow = relationship("WorkflowSession", back_populates="sandbox_sessions")

    __table_args__ = (
        Index("idx_sandbox_sessions_workflow", "workflow_id"),
        Index("idx_sandbox_sessions_status", "status"),
    )
