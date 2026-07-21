"""Base agent interface for The Hive."""

from abc import ABC, abstractmethod
from typing import Any

from core.llm.providers import LLMProvider, get_llm_provider
from core.orchestrator.state import WorkflowState


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

    async def build_enhanced_prompt(
        self,
        base_prompt: str,
        state: WorkflowState,
        context_limit: int = 3,
    ) -> str:
        """Build enhanced prompt with context injection.

        Args:
            base_prompt: Base prompt for the agent
            state: Current workflow state
            context_limit: Maximum context items to include

        Returns:
            Enhanced prompt with context
        """
        # Check if we have relevant context from previous stages
        context_parts = []

        # Add specification context if available
        if hasattr(state, "spec_artifact") and state.spec_artifact:
            context_parts.append("Specification: " + str(state.spec_artifact.get("title", "")))

        # Add design context if available
        if hasattr(state, "design_artifact") and state.design_artifact:
            context_parts.append("Design: " + str(state.design_artifact.get("modules", [])))

        # Add previous decisions if available
        if hasattr(state, "decisions") and state.decisions:
            recent_decisions = state.decisions[-context_limit:]
            for decision in recent_decisions:
                context_parts.append(f"Previous decision: {decision.get('decision_type', '')}")

        # Build enhanced prompt
        if context_parts:
            context_section = "\n\nRelevant Context:\n" + "\n".join(context_parts)
            enhanced_prompt = base_prompt + context_section
        else:
            enhanced_prompt = base_prompt

        return enhanced_prompt

    async def get_similar_decisions(
        self, query: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """Get similar decisions from cognitive memory.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of similar decisions
        """
        try:
            from memory.vectorstore.cognitive_memory import get_cognitive_memory

            cognitive_memory = get_cognitive_memory()
            similar_decisions = await cognitive_memory.search_similar_decisions(
                query=query,
                agent_type=self.agent_type,
                limit=limit,
            )
            return similar_decisions
        except Exception:
            # Return empty list if memory access fails
            return []
