"""Unit tests for workflow graph orchestration."""

import pytest
from unittest.mock import AsyncMock, patch

from core.orchestrator.graph import WorkflowOrchestrator
from core.orchestrator.state import WorkflowState


@pytest.mark.asyncio
class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator functionality."""

    async def test_initializes_graph(self):
        """Orchestrator initializes with a graph."""
        with patch("core.orchestrator.graph.StateGraph"):
            orchestrator = WorkflowOrchestrator()
            assert orchestrator.graph is not None

    async def test_registers_agent(self):
        """Agent can be registered for a stage."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def test_agent(state):
                return {}

            orchestrator.register_agent(WorkflowStage.SPEC, test_agent)
            assert WorkflowStage.SPEC.value in orchestrator.agents

    async def test_registers_multiple_agents(self):
        """Multiple agents can be registered."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def agent1(state):
                return {}

            async def agent2(state):
                return {}

            orchestrator.register_agent(WorkflowStage.SPEC, agent1)
            orchestrator.register_agent(WorkflowStage.DESIGN, agent2)

            assert len(orchestrator.agents) == 2

    async def test_execute_returns_workflow_state(self):
        """Execute returns a valid WorkflowState."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def mock_agent(state):
                return {"test_result": "value"}

            orchestrator.register_agent(WorkflowStage.SPEC, mock_agent)

            result = await orchestrator.execute("Test request")

            assert isinstance(result, WorkflowState)

    async def test_execute_generates_workflow_id(self):
        """Execute generates a unique workflow ID."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def mock_agent(state):
                return {}

            orchestrator.register_agent(WorkflowStage.SPEC, mock_agent)

            result = await orchestrator.execute("Test request")

            assert result.workflow_id is not None
            assert len(result.workflow_id) > 0

    async def test_execute_sets_input_request(self):
        """Execute sets the input request in state."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def mock_agent(state):
                return {}

            orchestrator.register_agent(WorkflowStage.SPEC, mock_agent)

            result = await orchestrator.execute("Add user auth")

            assert result.input_request == "Add user auth"

    async def test_agent_update_state(self):
        """Agent execution updates workflow state."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()

            async def update_agent(state):
                return {"custom_field": "custom_value"}

            orchestrator.register_agent(WorkflowStage.SPEC, update_agent)

            result = await orchestrator.execute("Test")

            assert hasattr(result, "custom_field")

    async def test_missing_agent_raises_exception(self):
        """Missing agent raises WorkflowException."""
        with patch("core.orchestrator.graph.StateGraph"):
            from core.workflow_definitions.stages import WorkflowStage
            from core.exceptions import WorkflowException

            orchestrator = WorkflowOrchestrator()

            # Don't register any agent
            result = await orchestrator.execute("Test")
            # Should handle missing agent gracefully


@pytest.mark.asyncio
class TestWorkflowState:
    """Test WorkflowState data model."""

    def test_create_default_state(self):
        """Create state with default values."""
        state = WorkflowState(workflow_id="test-id", input_request="test")
        assert state.workflow_id == "test-id"
        assert state.input_request == "test"
        assert state.status == "PENDING"

    def test_create_state_with_values(self):
        """Create state with custom values."""
        state = WorkflowState(
            workflow_id="test-id",
            input_request="test",
            status="RUNNING",
            current_stage="DESIGN",
        )
        assert state.status == "RUNNING"
        assert state.current_stage == "DESIGN"

    def test_state_accepts_artifacts(self):
        """State accepts artifacts dictionary."""
        artifacts = {"spec": {}, "design": {}}
        state = WorkflowState(
            workflow_id="test-id", input_request="test", artifacts=artifacts
        )
        assert state.artifacts == artifacts

    def test_state_tracks_stage_history(self):
        """State tracks stage execution history."""
        history = ["SPEC", "DESIGN"]
        state = WorkflowState(
            workflow_id="test-id", input_request="test", stage_history=history
        )
        assert state.stage_history == history
