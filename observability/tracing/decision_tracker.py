"""Decision provenance tracking for The Hive."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel


class DecisionRecord(BaseModel):
    """Record of an agent decision for provenance tracking."""

    model_config = {"arbitrary_types_allowed": True}

    decision_id: str
    agent_type: str
    timestamp: datetime
    decision_type: str
    input_context: dict[str, Any]
    output_decision: dict[str, Any]
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    dependencies: Optional[list[str]] = None
    workflow_id: Optional[str] = None


class DecisionTracker:
    """Track all agent decisions for provenance and observability."""

    def __init__(self):
        """Initialize decision tracker."""
        self.decisions: dict[str, DecisionRecord] = {}

    def record_decision(
        self,
        agent_type: str,
        decision_type: str,
        input_context: dict[str, Any],
        output_decision: dict[str, Any],
        confidence: Optional[float] = None,
        rationale: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
        workflow_id: Optional[str] = None,
    ) -> str:
        """Record an agent decision.

        Args:
            agent_type: Type of agent making the decision
            decision_type: Type of decision
            input_context: Input to decision
            output_decision: Output of decision
            confidence: Confidence score (0-1)
            rationale: Textual explanation
            dependencies: IDs of dependent decisions
            workflow_id: Associated workflow ID

        Returns:
            Decision ID
        """
        decision_id = str(uuid.uuid4())

        record = DecisionRecord(
            decision_id=decision_id,
            agent_type=agent_type,
            timestamp=datetime.now(timezone.utc),
            decision_type=decision_type,
            input_context=input_context,
            output_decision=output_decision,
            confidence=confidence,
            rationale=rationale,
            dependencies=dependencies or [],
            workflow_id=workflow_id,
        )

        self.decisions[decision_id] = record
        return decision_id

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Get a decision by ID.

        Args:
            decision_id: Decision ID

        Returns:
            Decision record or None
        """
        return self.decisions.get(decision_id)

    def get_workflow_decisions(self, workflow_id: str) -> list[DecisionRecord]:
        """Get all decisions for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of decision records
        """
        return [
            d
            for d in self.decisions.values()
            if d.workflow_id == workflow_id
        ]

    def get_agent_decisions(
        self, agent_type: str, workflow_id: Optional[str] = None
    ) -> list[DecisionRecord]:
        """Get all decisions by an agent.

        Args:
            agent_type: Agent type
            workflow_id: Optional workflow ID filter

        Returns:
            List of decision records
        """
        decisions = [
            d
            for d in self.decisions.values()
            if d.agent_type == agent_type
        ]

        if workflow_id:
            decisions = [d for d in decisions if d.workflow_id == workflow_id]
        return decisions
