"""Agent telemetry tracking for observability."""

import time
import threading
from typing import Any, Optional
from pydantic import BaseModel


class AgentState(BaseModel):
    """State tracking for a single agent."""

    model_config = {"arbitrary_types_allowed": True}

    agent_type: str
    workflow_id: Optional[str] = None
    status: str = "IDLE"
    tokens_consumed: int = 0
    last_heartbeat: Optional[float] = None
    current_task: Optional[str] = None
    error_count: int = 0
    start_time: Optional[float] = None
    state_data: dict[str, Any] = {}


class AgentTelemetryTracker:
    """Track agent telemetry and state."""

    def __init__(self):
        """Initialize telemetry tracker."""
        self._lock = threading.Lock()
        self._agent_states: dict[str, AgentState] = {}
        self._tokens_by_agent: dict[str, int] = {}

    def start_agent_task(
        self, agent_type: str, workflow_id: str, task: str
    ) -> None:
        """Mark start of agent task.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID
            task: Task description
        """
        with self._lock:
            agent_id = f"{workflow_id}:{agent_type}"

            state = self._agent_states.get(agent_id)
            if state is None:
                state = AgentState(agent_type=agent_type, workflow_id=workflow_id)
                self._agent_states[agent_id] = state

            state.status = "ACTIVE"
            state.current_task = task
            state.start_time = time.time()
            state.last_heartbeat = time.time()

    def complete_agent_task(
        self, agent_type: str, workflow_id: str, tokens: int = 0
    ) -> None:
        """Mark completion of agent task.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID
            tokens: Tokens consumed
        """
        with self._lock:
            agent_id = f"{workflow_id}:{agent_type}"

            state = self._agent_states.get(agent_id)
            if state is None:
                return

            state.status = "IDLE"
            state.current_task = None
            state.tokens_consumed += tokens
            state.last_heartbeat = time.time()

            # Update total tokens by agent type
            self._tokens_by_agent[agent_type] = (
                self._tokens_by_agent.get(agent_type, 0) + tokens
            )

    def record_agent_error(
        self, agent_type: str, workflow_id: str, error: str
    ) -> None:
        """Record an agent error.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID
            error: Error message
        """
        with self._lock:
            agent_id = f"{workflow_id}:{agent_type}"

            state = self._agent_states.get(agent_id)
            if state is None:
                return

            state.status = "ERROR"
            state.error_count += 1
            state.state_data["last_error"] = error
            state.last_heartbeat = time.time()

    def update_heartbeat(
        self, agent_type: str, workflow_id: str
    ) -> None:
        """Update agent heartbeat timestamp.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID
        """
        with self._lock:
            agent_id = f"{workflow_id}:{agent_type}"

            state = self._agent_states.get(agent_id)
            if state is None:
                return

            state.last_heartbeat = time.time()

    def get_agent_state(
        self, agent_type: str, workflow_id: str
    ) -> Optional[AgentState]:
        """Get current state for an agent.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID

        Returns:
            Agent state or None
        """
        with self._lock:
            agent_id = f"{workflow_id}:{agent_type}"
            return self._agent_states.get(agent_id)

    def get_workflow_agents(
        self, workflow_id: str
    ) -> dict[str, AgentState]:
        """Get all agent states for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dictionary of agent_type -> AgentState
        """
        with self._lock:
            return {
                agent_type: state
                for agent_id, state in self._agent_states.items()
                if state.workflow_id == workflow_id
                for agent_type in [agent_type.split(":")[-1]]
            }

    def get_total_tokens(self, agent_type: str) -> int:
        """Get total tokens consumed by an agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Total tokens consumed
        """
        with self._lock:
            return self._tokens_by_agent.get(agent_type, 0)

    def get_resource_usage(self, agent_type: str, workflow_id: str) -> dict[str, Any]:
        """Get resource usage metrics for an agent.

        Args:
            agent_type: Type of agent
            workflow_id: Workflow ID

        Returns:
            Resource usage metrics
        """
        state = self.get_agent_state(agent_type, workflow_id)
        if state is None:
            return {}

        duration = 0
        if state.start_time:
            duration = time.time() - state.start_time

        return {
            "agent_type": agent_type,
            "workflow_id": workflow_id,
            "status": state.status,
            "current_task": state.current_task,
            "duration_seconds": duration,
            "tokens_consumed": state.tokens_consumed,
            "error_count": state.error_count,
            "last_heartbeat": state.last_heartbeat,
        }


# Global telemetry tracker instance
_telemetry_tracker: Optional[AgentTelemetryTracker] = None


def get_telemetry_tracker() -> AgentTelemetryTracker:
    """Get global telemetry tracker instance.

    Returns:
        Telemetry tracker instance
    """
    global _telemetry_tracker
    if _telemetry_tracker is None:
        _telemetry_tracker = AgentTelemetryTracker()
    return _telemetry_tracker
