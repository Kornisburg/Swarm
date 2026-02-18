"""Unit tests for workflow state."""

import pytest
from pydantic import ValidationError

from core.orchestrator.state import WorkflowState


class TestWorkflowStateValidation:
    """Test WorkflowState validation."""

    def test_requires_workflow_id(self):
        """WorkflowState requires workflow_id."""
        with pytest.raises(ValidationError):
            WorkflowState(input_request="test")

    def test_requires_input_request(self):
        """WorkflowState requires input_request."""
        with pytest.raises(ValidationError):
            WorkflowState(workflow_id="test-id")

    def test_accepts_valid_data(self):
        """WorkflowState accepts valid data."""
        state = WorkflowState(
            workflow_id="test-id",
            input_request="Add user authentication",
            status="PENDING",
        )
        assert state.workflow_id == "test-id"
        assert state.input_request == "Add user authentication"

    def test_default_status_is_pending(self):
        """Default status is PENDING."""
        state = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        assert state.status == "PENDING"

    def test_default_stage_history_is_empty(self):
        """Default stage_history is empty list."""
        state = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        assert state.stage_history == []

    def test_default_artifacts_is_empty_dict(self):
        """Default artifacts is empty dict."""
        state = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        assert state.artifacts == {}


class TestWorkflowStateFields:
    """Test WorkflowState field behavior."""

    def test_status_accepts_valid_values(self):
        """Status accepts valid workflow status values."""
        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
        for status in valid_statuses:
            state = WorkflowState(
                workflow_id="test-id", input_request="test", status=status
            )
            assert state.status == status

    def test_workflow_id_is_string(self):
        """workflow_id must be a string."""
        state = WorkflowState(
            workflow_id=123, input_request="test"
        )
        # Pydantic coerces to string
        assert isinstance(state.workflow_id, str)

    def test_artifacts_dict_accepts_any_values(self):
        """artifacts dict accepts any values."""
        artifacts = {
            "spec": {"title": "Test"},
            "design": ["module1", "module2"],
            "code": "print('hello')",
        }
        state = WorkflowState(
            workflow_id="test-id", input_request="test", artifacts=artifacts
        )
        assert state.artifacts == artifacts


class TestWorkflowStateImmutability:
    """Test WorkflowState behavior with updates."""

    def test_state_can_be_copied_with_updates(self):
        """State can be copied with field updates."""
        original = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        updated = original.model_copy(update={"status": "RUNNING"})
        assert original.status == "PENDING"
        assert updated.status == "RUNNING"
        assert original.workflow_id == updated.workflow_id


class TestWorkflowStateJsonSerialization:
    """Test WorkflowState JSON serialization."""

    def test_can_serialize_to_dict(self):
        """State can be serialized to dictionary."""
        state = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        data = state.model_dump()
        assert isinstance(data, dict)
        assert "workflow_id" in data
        assert "input_request" in data

    def test_can_serialize_to_json(self):
        """State can be serialized to JSON."""
        state = WorkflowState(
            workflow_id="test-id", input_request="test"
        )
        json_str = state.model_dump_json()
        assert isinstance(json_str, str)
        assert "workflow_id" in json_str

    def test_can_deserialize_from_dict(self):
        """State can be deserialized from dictionary."""
        data = {
            "workflow_id": "test-id",
            "input_request": "test",
            "status": "RUNNING",
        }
        state = WorkflowState(**data)
        assert state.workflow_id == "test-id"
        assert state.status == "RUNNING"
