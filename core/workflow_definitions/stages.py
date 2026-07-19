"""Workflow stage definitions for The Hive."""

from enum import Enum
from typing import Optional


class WorkflowStage(str, Enum):
    """Workflow execution stages."""

    SPEC = "spec"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    DEPLOY = "deploy"


class StageOrder:
    """Define the order of workflow stages."""

    ORDER = [
        WorkflowStage.SPEC,
        WorkflowStage.DESIGN,
        WorkflowStage.IMPLEMENT,
        WorkflowStage.REVIEW,
        WorkflowStage.TEST,
        WorkflowStage.DEPLOY,
    ]

    @classmethod
    def get_next_stage(cls, current: WorkflowStage) -> Optional[WorkflowStage]:
        """Get the next stage in the workflow.

        Args:
            current: Current stage

        Returns:
            Next stage or None if current is the last stage
        """
        try:
            index = cls.ORDER.index(current)
            if index + 1 < len(cls.ORDER):
                return cls.ORDER[index + 1]
        except ValueError:
            pass
        return None

    @classmethod
    def get_first_stage(cls) -> WorkflowStage:
        """Get the first stage in the workflow.

        Returns:
            First stage
        """
        return cls.ORDER[0]
