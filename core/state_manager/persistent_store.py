"""PostgreSQL persistent store for completed workflows."""

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...memory.postgres.client import get_postgres_client
from ...memory.postgres.models import (
    WorkflowSession,
    DecisionRecord,
    Artifact,
    AgentState,
)
from ...exceptions import WorkflowException


class PersistentStore:
    """PostgreSQL-based persistent store for workflow state."""

    def __init__(self):
        """Initialize persistent store."""
        self.postgres = get_postgres_client()

    async def save_workflow(
        self,
        workflow_id: str,
        input_request: str,
        status: str,
        current_stage: str,
        state: dict[str, Any],
    ) -> WorkflowSession:
        """Save or update workflow session.

        Args:
            workflow_id: Workflow identifier
            input_request: Original user request
            status: Workflow status
            current_stage: Current stage
            state: Full workflow state

        Returns:
            Saved workflow session
        """
        try:
            async with self.postgres.get_session() as session:
                # Check if workflow exists
                result = await session.execute(
                    select(WorkflowSession).where(WorkflowSession.id == workflow_id)
                )
                workflow = result.scalar_one_or_none()

                if workflow:
                    # Update existing
                    workflow.status = status
                    workflow.current_stage = current_stage
                    workflow.state_json = json.dumps(state)
                    workflow.updated_at = datetime.utcnow()
                else:
                    # Create new
                    workflow = WorkflowSession(
                        id=workflow_id,
                        input_request=input_request,
                        status=status,
                        current_stage=current_stage,
                        state_json=json.dumps(state),
                    )
                    session.add(workflow)

                await session.commit()
                await session.refresh(workflow)
                return workflow
        except Exception as e:
            raise WorkflowException(f"Failed to save workflow: {str(e)}")

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowSession]:
        """Retrieve workflow session.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow session or None
        """
        try:
            async with self.postgres.get_session() as session:
                result = await session.execute(
                    select(WorkflowSession).where(WorkflowSession.id == workflow_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise WorkflowException(f"Failed to get workflow: {str(e)}")

    async def get_workflow_state(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """Get workflow state JSON.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow state dictionary or None
        """
        workflow = await self.get_workflow(workflow_id)
        if workflow:
            return json.loads(workflow.state_json)
        return None

    async def save_decision(
        self,
        workflow_id: str,
        agent_type: str,
        decision_type: str,
        decision_data: dict[str, Any],
        confidence: float,
        rationale: str,
    ) -> DecisionRecord:
        """Save agent decision record.

        Args:
            workflow_id: Workflow identifier
            agent_type: Agent type
            decision_type: Decision type
            decision_data: Decision content
            confidence: Confidence score (0-1)
            rationale: Decision rationale

        Returns:
            Saved decision record
        """
        try:
            async with self.postgres.get_session() as session:
                decision = DecisionRecord(
                    workflow_id=workflow_id,
                    agent_type=agent_type,
                    decision_type=decision_type,
                    decision_data=json.dumps(decision_data),
                    confidence=confidence,
                    rationale=rationale,
                )
                session.add(decision)
                await session.commit()
                await session.refresh(decision)
                return decision
        except Exception as e:
            raise WorkflowException(f"Failed to save decision: {str(e)}")

    async def get_decisions(
        self, workflow_id: str, agent_type: Optional[str] = None
    ) -> list[DecisionRecord]:
        """Get workflow decisions.

        Args:
            workflow_id: Workflow identifier
            agent_type: Optional filter by agent type

        Returns:
            List of decision records
        """
        try:
            async with self.postgres.get_session() as session:
                query = select(DecisionRecord).where(
                    DecisionRecord.workflow_id == workflow_id
                )
                if agent_type:
                    query = query.where(DecisionRecord.agent_type == agent_type)
                query = query.order_by(DecisionRecord.timestamp)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise WorkflowException(f"Failed to get decisions: {str(e)}")

    async def save_artifact(
        self,
        workflow_id: str,
        artifact_type: str,
        content: dict[str, Any],
        version: int = 1,
    ) -> Artifact:
        """Save workflow artifact.

        Args:
            workflow_id: Workflow identifier
            artifact_type: Artifact type (SPEC, DESIGN, CODE, etc.)
            content: Artifact content
            version: Artifact version

        Returns:
            Saved artifact
        """
        try:
            async with self.postgres.get_session() as session:
                artifact = Artifact(
                    workflow_id=workflow_id,
                    artifact_type=artifact_type,
                    content_json=json.dumps(content),
                    version=version,
                )
                session.add(artifact)
                await session.commit()
                await session.refresh(artifact)
                return artifact
        except Exception as e:
            raise WorkflowException(f"Failed to save artifact: {str(e)}")

    async def get_artifacts(
        self, workflow_id: str, artifact_type: Optional[str] = None
    ) -> list[Artifact]:
        """Get workflow artifacts.

        Args:
            workflow_id: Workflow identifier
            artifact_type: Optional filter by type

        Returns:
            List of artifacts
        """
        try:
            async with self.postgres.get_session() as session:
                query = select(Artifact).where(Artifact.workflow_id == workflow_id)
                if artifact_type:
                    query = query.where(Artifact.artifact_type == artifact_type)
                query = query.order_by(Artifact.created_at)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise WorkflowException(f"Failed to get artifacts: {str(e)}")

    async def save_agent_state(
        self,
        workflow_id: str,
        agent_type: str,
        status: str,
        tokens_consumed: int,
        state_data: dict[str, Any],
    ) -> AgentState:
        """Save agent state record.

        Args:
            workflow_id: Workflow identifier
            agent_type: Agent type
            status: Agent status
            tokens_consumed: Tokens used
            state_data: Additional state data

        Returns:
            Saved agent state
        """
        try:
            async with self.postgres.get_session() as session:
                agent_state = AgentState(
                    workflow_id=workflow_id,
                    agent_type=agent_type,
                    status=status,
                    tokens_consumed=tokens_consumed,
                    state_json=json.dumps(state_data),
                )
                session.add(agent_state)
                await session.commit()
                await session.refresh(agent_state)
                return agent_state
        except Exception as e:
            raise WorkflowException(f"Failed to save agent state: {str(e)}")

    async def get_agent_states(self, workflow_id: str) -> list[AgentState]:
        """Get workflow agent states.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of agent states
        """
        try:
            async with self.postgres.get_session() as session:
                query = select(AgentState).where(
                    AgentState.workflow_id == workflow_id
                ).order_by(AgentState.updated_at)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise WorkflowException(f"Failed to get agent states: {str(e)}")

    async def health_check(self) -> bool:
        """Check PostgreSQL health.

        Returns:
            True if healthy
        """
        return self.postgres.health_check()


# Global persistent store instance
_persistent_store: Optional[PersistentStore] = None


def get_persistent_store() -> PersistentStore:
    """Get global persistent store instance.

    Returns:
        Persistent store instance
    """
    global _persistent_store
    if _persistent_store is None:
        _persistent_store = PersistentStore()
    return _persistent_store
