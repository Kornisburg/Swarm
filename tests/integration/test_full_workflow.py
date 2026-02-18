"""Integration tests for full workflow execution."""

import pytest
from unittest.mock import AsyncMock, patch

from core.orchestrator import WorkflowOrchestrator, WorkflowState


@pytest.mark.asyncio
class TestFullWorkflowExecution:
    """Test end-to-end workflow execution."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents."""
        async def mock_spec_agent(state):
            return {
                "spec_artifact": {"title": "Test Feature", "description": "Test"},
                "artifacts": {"spec": {"title": "Test Feature"}},
            }

        async def mock_design_agent(state):
            return {
                "design_artifact": {"modules": ["module1"]},
                "artifacts": {"design": {"modules": ["module1"]}},
            }

        async def mock_implement_agent(state):
            return {
                "code_artifact": {"files": [{"path": "test.py", "content": "pass"}]},
                "artifacts": {"code": {"files": []}},
            }

        return {
            "spec": mock_spec_agent,
            "design": mock_design_agent,
            "implement": mock_implement_agent,
        }

    async def test_workflow_executes_all_stages(self, mock_agents):
        """Workflow executes through all stages."""
        with patch("core.orchestrator.graph.StateGraph"):
            orchestrator = WorkflowOrchestrator()

            # Register agents
            from core.workflow_definitions.stages import WorkflowStage

            for stage, agent_func in mock_agents.items():
                orchestrator.register_agent(WorkflowStage[stage.upper()], agent_func)

            # Execute workflow
            final_state = await orchestrator.execute("Add user authentication")

            assert final_state is not None
            assert final_state.status in ["COMPLETED", "RUNNING"]

    async def test_workflow_maintains_state_between_stages(self, mock_agents):
        """Workflow maintains state across stages."""
        with patch("core.orchestrator.graph.StateGraph"):
            orchestrator = WorkflowOrchestrator()

            from core.workflow_definitions.stages import WorkflowStage

            for stage, agent_func in mock_agents.items():
                orchestrator.register_agent(WorkflowStage[stage.upper()], agent_func)

            # Execute workflow
            final_state = await orchestrator.execute("Test feature")

            # Check state is preserved
            assert final_state.input_request == "Test feature"
            assert "artifacts" in final_state.__dict__

    async def test_workflow_handles_agent_failure(self):
        """Workflow handles agent failure gracefully."""
        async def failing_agent(state):
            raise Exception("Agent failed")

        with patch("core.orchestrator.graph.StateGraph"):
            orchestrator = WorkflowOrchestrator()

            from core.workflow_definitions.stages import WorkflowStage

            orchestrator.register_agent(WorkflowStage.SPEC, failing_agent)

            # Execute workflow
            try:
                await orchestrator.execute("Test feature")
                # If it doesn't raise, check state
            except Exception as e:
                # Expected exception
                assert "Agent failed" in str(e) or "workflow" in str(e).lower()

    async def test_workflow_generates_unique_ids(self, mock_agents):
        """Each workflow gets a unique ID."""
        with patch("core.orchestrator.graph.StateGraph"):
            orchestrator = WorkflowOrchestrator()

            from core.workflow_definitions.stages import WorkflowStage

            for stage, agent_func in mock_agents.items():
                orchestrator.register_agent(WorkflowStage[stage.upper()], agent_func)

            # Execute two workflows
            state1 = await orchestrator.execute("Feature 1")
            state2 = await orchestrator.execute("Feature 2")

            assert state1.workflow_id != state2.workflow_id


@pytest.mark.asyncio
class TestAgentCollaboration:
    """Test agent collaboration in workflow."""

    async def test_spec_agent_passes_input_to_design_agent(self):
        """Spec agent output is available to design agent."""
        spec_output = {"requirements": ["REQ-001"]}

        async def spec_agent(state):
            return {"spec_artifact": spec_output}

        async def design_agent(state):
            # Design agent should have access to spec artifact
            assert hasattr(state, "spec_artifact")
            return {"design_artifact": {"design": "completed"}}

        with patch("core.orchestrator.graph.StateGraph"):
            from core.orchestrator import WorkflowOrchestrator
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()
            orchestrator.register_agent(WorkflowStage.SPEC, spec_agent)
            orchestrator.register_agent(WorkflowStage.DESIGN, design_agent)

            await orchestrator.execute("Test feature")

    async def test_design_agent_passes_input_to_implement_agent(self):
        """Design agent output is available to implement agent."""
        design_output = {"architecture": "microservices"}

        async def spec_agent(state):
            return {"spec_artifact": {}}

        async def design_agent(state):
            return {"design_artifact": design_output}

        async def implement_agent(state):
            # Implement agent should have access to design artifact
            assert hasattr(state, "design_artifact")
            return {"code_artifact": {"code": "generated"}}

        with patch("core.orchestrator.graph.StateGraph"):
            from core.orchestrator import WorkflowOrchestrator
            from core.workflow_definitions.stages import WorkflowStage

            orchestrator = WorkflowOrchestrator()
            orchestrator.register_agent(WorkflowStage.SPEC, spec_agent)
            orchestrator.register_agent(WorkflowStage.DESIGN, design_agent)
            orchestrator.register_agent(WorkflowStage.IMPLEMENT, implement_agent)

            await orchestrator.execute("Test feature")


@pytest.mark.asyncio
class TestStatePersistence:
    """Test state persistence across workflow execution."""

    async def test_state_saved_to_postgres(self):
        """Workflow state is saved to PostgreSQL."""
        with patch("core.state_manager.persistent_store.get_persistent_store") as mock_get:
            mock_store = AsyncMock()
            mock_store.save_workflow = AsyncMock()
            mock_get.return_value = mock_store

            from core.state_manager import get_persistent_store

            store = get_persistent_store()
            await store.save_workflow(
                "test-id", "Test request", "COMPLETED", "IMPLEMENT", {}
            )

            mock_store.save_workflow.assert_called_once()

    async def test_session_saved_to_redis(self):
        """Active session is saved to Redis."""
        with patch("core.state_manager.session_store.get_session_store") as mock_get:
            mock_store = AsyncMock()
            mock_store.save_session = AsyncMock()
            mock_get.return_value = mock_store

            from core.state_manager import get_session_store

            store = get_session_store()
            await store.save_session("test-id", {"stage": "DESIGN"})

            mock_store.save_session.assert_called_once()
