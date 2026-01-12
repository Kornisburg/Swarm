"""LangSmith trace exporter for The Hive."""

import os
from typing import Any, Optional

from langsmith import Client
from langchain_core.runnables import RunnableLambda


class LangSmithExporter:
    """LangSmith integration for LLM tracing."""

    def __init__(self):
        """Initialize LangSmith exporter."""
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "hive-mvp")
        self.client: Optional[Client] = None

        if self.api_key:
            self.client = Client(api_key=self.api_key)

    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled.

        Returns:
            True if enabled
        """
        return (
            os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
            and self.client is not None
        )

    def trace_agent_call(
        self,
        agent_type: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        """Trace an agent call to LangSmith.

        Args:
            agent_type: Type of agent
            input_data: Agent input
            output_data: Agent output
            metadata: Additional metadata
        """
        if not self.is_enabled():
            return

        # LangSmith automatic tracing handles this when using LangChain
        # This is for custom tracing if needed
        pass

    def create_run(
        self,
        name: str,
        inputs: dict[str, Any],
        run_type: str = "chain",
    ) -> Optional[str]:
        """Create a new run in LangSmith.

        Args:
            name: Run name
            inputs: Run inputs
            run_type: Type of run

        Returns:
            Run ID or None
        """
        if not self.is_enabled():
            return None

        # LangSmith handles this automatically
        # This is a placeholder for manual run creation if needed
        return None
