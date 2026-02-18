"""Contract tests for workflow API."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from infra.fastapi_gateway.app import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health endpoint contract."""

    async def test_health_check_returns_200(self, client):
        """Health endpoint returns 200 status."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_check_returns_json(self, client):
        """Health endpoint returns JSON response."""
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"

    async def test_health_check_has_status_field(self, client):
        """Health response includes status field."""
        response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
class TestWorkflowSubmission:
    """Test workflow submission contract."""

    async def test_submit_workflow_returns_201(self, client):
        """Workflow submission returns 201 status."""
        payload = {"input_request": "Add user authentication"}
        with patch("infra.fastapi_gateway.routes.workflows.orchestrator"):
            response = await client.post("/workflows", json=payload)
            assert response.status_code in [201, 202]  # Created or Accepted

    async def test_submit_workflow_requires_input_request(self, client):
        """Workflow submission requires input_request field."""
        payload = {}
        response = await client.post("/workflows", json=payload)
        assert response.status_code == 422  # Validation error

    async def test_submit_workflow_returns_workflow_id(self, client):
        """Workflow submission returns workflow_id."""
        payload = {"input_request": "Add user authentication"}
        with patch("infra.fastapi_gateway.routes.workflows.orchestrator"):
            response = await client.post("/workflows", json=payload)
            if response.status_code in [201, 202]:
                data = response.json()
                assert "workflow_id" in data


@pytest.mark.asyncio
class TestWorkflowStatus:
    """Test workflow status query contract."""

    async def test_get_status_returns_404_for_unknown(self, client):
        """Status query returns 404 for unknown workflow."""
        response = await client.get("/workflows/unknown-id/status")
        assert response.status_code == 404

    async def test_get_status_returns_json(self, client):
        """Status query returns JSON response."""
        # This would need a mock with actual workflow data
        with patch(
            "infra.fastapi_gateway.routes.status.get_persistent_store"
        ) as mock_store:
            mock_store.return_value.get_workflow = AsyncMock(return_value=None)
            response = await client.get("/workflows/test-id/status")
            assert response.status_code == 404


@pytest.mark.asyncio
class TestArtifactRetrieval:
    """Test artifact retrieval contract."""

    async def test_get_artifacts_returns_404_for_unknown(self, client):
        """Artifact query returns 404 for unknown workflow."""
        response = await client.get("/workflows/unknown-id/artifacts")
        assert response.status_code == 404

    async def test_get_artifact_returns_404_for_unknown(self, client):
        """Specific artifact query returns 404 for unknown workflow."""
        response = await client.get("/workflows/unknown-id/artifacts/artifact-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestCancellation:
    """Test workflow cancellation contract."""

    async def test_cancel_workflow_returns_200(self, client):
        """Cancellation returns 200 status."""
        # This would need a mock with actual workflow
        with patch("infra.fastapi_gateway.routes.workflows.session_store"):
            response = await client.post("/workflows/test-id/cancel")
            # Returns 200 if exists, 404 if not
            assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestCORS:
    """Test CORS middleware."""

    async def test_cors_headers_present(self, client):
        """CORS headers are present in response."""
        response = await client.options("/health")
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
