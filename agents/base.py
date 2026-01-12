"""Base agent interface for The Hive."""

from abc import ABC, abstractmethod
from typing import Any

from ..orchestrator.state import WorkflowState
from ..llm.providers import LLMProvider, get_llm_provider


class BaseAgent(ABC):
    """Base class for all agents in The Hive."""

    def __init__(self):
        """Initialize the agent."""
        self.llm: LLMProvider = get_llm_provider()
        self.agent_type = self.__class__.__name__.replace("Agent", "").upper()

    @abstractmethod
    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the agent's logic.

        Args:
            state: Current workflow state

        Returns:
            Updated state fragment
        """
        pass

    async def invoke(self, state: WorkflowState) -> dict[str, Any]:
        """Invoke the agent with error handling.

        Args:
            state: Current workflow state

        Returns:
            Updated state fragment
        """
        try:
            result = await self.execute(state)
            return result
        except Exception as e:
            return {
                "error_message": f"{self.agent_type} failed: {str(e)}",
                "status": "FAILED",
            }
