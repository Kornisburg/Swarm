"""Unit tests for SpecAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from agents.spec.spec_agent import SpecAgent
from core.orchestrator.state import WorkflowState


@pytest.mark.asyncio
class TestSpecAgent:
    """Test SpecAgent functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        with patch("agents.base.get_llm_provider") as mock_get:
            mock_llm = AsyncMock()
            mock_llm.complete = AsyncMock(
                return_value='{"title": "Test Feature", "description": "Test"}'
            )
            mock_get.return_value = mock_llm
            yield mock_llm

    async def test_agent_initializes(self, mock_llm):
        """Agent initializes successfully."""
        agent = SpecAgent()
        assert agent is not None
        assert agent.llm is not None
        assert agent.agent_type == "SPEC"

    async def test_execute_returns_spec_artifact(self, mock_llm):
        """execute returns a spec artifact."""
        agent = SpecAgent()
        state = WorkflowState(
            workflow_id="test-id", input_request="Add user authentication"
        )

        result = await agent.execute(state)

        assert "spec_artifact" in result
        assert "artifacts" in result

    async def test_parse_spec_response_handles_json(self, mock_llm):
        """_parse_spec_response handles JSON response."""
        agent = SpecAgent()
        json_response = '{"title": "Test", "description": "Test desc"}'

        result = agent._parse_spec_response(json_response)

        assert result["title"] == "Test"
        assert result["description"] == "Test desc"

    async def test_parse_spec_response_handles_extra_text(self, mock_llm):
        """_parse_spec_response extracts JSON from text."""
        agent = SpecAgent()
        response = "Here's the spec:\n{\"title\": \"Test\"}\nThat's it!"

        result = agent._parse_spec_response(response)

        assert result["title"] == "Test"

    async def test_parse_spec_response_handles_malformed_json(self, mock_llm):
        """_parse_spec_response handles malformed JSON gracefully."""
        agent = SpecAgent()
        response = "This is not valid JSON"

        result = agent._parse_spec_response(response)

        assert "error" in result
        assert "raw_response" in result

    async def test_build_spec_prompt_includes_request(self, mock_llm):
        """_build_spec_prompt includes the feature request."""
        agent = SpecAgent()
        prompt = agent._build_spec_prompt("Add OAuth2 login")

        assert "Add OAuth2 login" in prompt

    async def test_build_spec_prompt_includes_json_structure(self, mock_llm):
        """_build_spec_prompt includes JSON structure instructions."""
        agent = SpecAgent()
        prompt = agent._build_spec_prompt("Test feature")

        assert "user_stories" in prompt
        assert "functional_requirements" in prompt
        assert "JSON" in prompt


@pytest.mark.asyncio
class TestSpecAgentIntegration:
    """Test SpecAgent with LLM integration."""

    async def test_execute_calls_llm_complete(self):
        """execute calls LLM complete method."""
        with patch("agents.base.get_llm_provider") as mock_get:
            mock_llm = AsyncMock()
            mock_llm.complete = AsyncMock(
                return_value='{"title": "Test", "description": "Test"}'
            )
            mock_get.return_value = mock_llm

            agent = SpecAgent()
            state = WorkflowState(
                workflow_id="test-id", input_request="Test"
            )

            await agent.execute(state)

            mock_llm.complete.assert_called_once()

    async def test_execute_passes_state_to_llm(self):
        """execute passes workflow state to LLM."""
        with patch("agents.base.get_llm_provider") as mock_get:
            mock_llm = AsyncMock()
            mock_llm.complete = AsyncMock(
                return_value='{"title": "Test", "description": "Test"}'
            )
            mock_get.return_value = mock_llm

            agent = SpecAgent()
            state = WorkflowState(
                workflow_id="test-id", input_request="Add user auth"
            )

            await agent.execute(state)

            call_args = mock_llm.complete.call_args
            assert "Add user auth" in str(call_args)
