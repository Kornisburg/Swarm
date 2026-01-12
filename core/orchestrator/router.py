"""Deterministic routing logic for The Hive orchestrator."""

from typing import Any, Optional

from ..workflow_definitions.stages import WorkflowStage
from ..exceptions import WorkflowException


class DeterministicRouter:
    """Deterministic routing between workflow stages."""

    @staticmethod
    def route_after_stage(stage: WorkflowStage, state: dict[str, Any]) -> str:
        """Determine next stage after current stage.

        Args:
            stage: Current workflow stage
            state: Current workflow state

        Returns:
            Next stage name or "end"

        Raises:
            WorkflowException: If routing fails
        """
        # Check for errors
        if state.get("error_message"):
            return "end"

        # Check for cancellation
        if state.get("status") == "CANCELLED":
            return "end"

        # Check for retry conditions
        if DeterministicRouter._should_retry(stage, state):
            return stage.value  # Retry current stage

        # Determine next stage
        next_stage = DeterministicRouter._get_next_stage(stage)
        return next_stage.value if next_stage else "end"

    @staticmethod
    def _should_retry(stage: WorkflowStage, state: dict[str, Any]) -> bool:
        """Check if current stage should be retried.

        Args:
            stage: Current stage
            state: Current workflow state

        Returns:
            True if should retry
        """
        # Retry on transient failures
        error = state.get("error_message", "")
        if "timeout" in error.lower() or "connection" in error.lower():
            retry_count = state.get("retry_count", 0)
            return retry_count < 3

        # Retry if required artifact missing
        required_artifacts = {
            WorkflowStage.SPEC: "spec_artifact",
            WorkflowStage.DESIGN: "design_artifact",
            WorkflowStage.IMPLEMENT: "code_artifact",
        }

        if stage in required_artifacts:
            if not state.get(required_artifacts[stage]):
                return True

        return False

    @staticmethod
    def _get_next_stage(stage: WorkflowStage) -> Optional[WorkflowStage]:
        """Get next stage in sequence.

        Args:
            stage: Current stage

        Returns:
            Next stage or None
        """
        stages = [
            WorkflowStage.SPEC,
            WorkflowStage.DESIGN,
            WorkflowStage.IMPLEMENT,
            WorkflowStage.REVIEW,
            WorkflowStage.TEST,
            WorkflowStage.DEPLOY,
        ]

        try:
            idx = stages.index(stage)
            if idx + 1 < len(stages):
                return stages[idx + 1]
        except ValueError:
            raise WorkflowException(f"Invalid stage: {stage}")

        return None

    @staticmethod
    def should_pause(state: dict[str, Any]) -> bool:
        """Check if workflow should pause for user input.

        Args:
            state: Current workflow state

        Returns:
            True if should pause
        """
        # Pause on approval requests
        if state.get("requires_approval"):
            return True

        # Pause on critical decisions
        if state.get("critical_decision"):
            return True

        return False
