"""LangSmith trace exporter for The Hive."""

import os
from typing import Any

from langsmith import Client


class LangSmithExporter:
    """LangSmith integration for LLM tracing."""

    def __init__(self):
        """Initialize LangSmith exporter."""
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "hive-mvp")
        self.client: Client | None = None

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

    def track_decision(self, decision_data: dict[str, Any]) -> None:
        """Track a decision via LangSmith.

        Args:
            decision_data: Decision data dictionary
        """
        if not self.is_enabled():
            return

        try:
            self.client.create_run(
                name=f"decision_{decision_data.get('decision_type', 'unknown')}",
                run_type="chain",
                inputs=decision_data.get("input", {}),
                outputs=decision_data.get("output", {}),
                extra={"agent_type": decision_data.get("agent_type", "UNKNOWN")},
            )
        except Exception:
            pass

    def create_run(
        self,
        name: str,
        inputs: dict[str, Any],
        run_type: str = "chain",
    ) -> str | None:
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
