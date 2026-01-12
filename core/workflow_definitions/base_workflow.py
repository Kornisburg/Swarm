"""Base workflow template for The Hive."""

from typing import Any, Optional

from .stages import WorkflowStage, StageOrder


class BaseWorkflow:
    """Base workflow template with common functionality."""

    def __init__(self):
        """Initialize base workflow."""
        self.stages = StageOrder.ORDER.copy()

    def get_stage(self, stage_name: str) -> Optional[WorkflowStage]:
        """Get stage by name.

        Args:
            stage_name: Stage name

        Returns:
            WorkflowStage or None
        """
        for stage in WorkflowStage:
            if stage.value == stage_name:
                return stage
        return None

    def is_valid_transition(self, from_stage: str, to_stage: str) -> bool:
        """Check if stage transition is valid.

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            True if transition is valid
        """
        from_idx = self.stages.index(self.get_stage(from_stage)) if from_stage else -1
        to_idx = self.stages.index(self.get_stage(to_stage)) if to_stage else -1
        return to_idx == from_idx + 1

    def get_remaining_stages(self, current_stage: Optional[str] = None) -> list[WorkflowStage]:
        """Get remaining stages after current stage.

        Args:
            current_stage: Current stage name

        Returns:
            List of remaining stages
        """
        if current_stage is None:
            return self.stages.copy()

        try:
            current_idx = self.stages.index(self.get_stage(current_stage))
            return self.stages[current_idx + 1 :]
        except (ValueError, IndexError):
            return []

    def should_continue(self, state: dict[str, Any]) -> tuple[bool, str]:
        """Determine if workflow should continue to next stage.

        Args:
            state: Current workflow state

        Returns:
            Tuple of (should_continue, next_stage)
        """
        if state.get("error_message"):
            return False, "failed"

        if state.get("status") == "CANCELLED":
            return False, "cancelled"

        current = state.get("current_stage")
        remaining = self.get_remaining_stages(current)

        if not remaining:
            return False, "completed"

        return True, remaining[0].value
