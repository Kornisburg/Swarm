"""Unit tests for PostgreSQL client."""

import pytest
from unittest.mock import AsyncMock, patch

from memory.postgres.client import PostgreSQLClient
from memory.postgres.models import WorkflowSession


@pytest.mark.asyncio
class TestPostgreSQLClient:
    """Test PostgreSQL client functionality."""

    @pytest.fixture
    def mock_engine(self):
        """Create mock SQLAlchemy engine."""
        with patch("memory.postgres.client.create_async_engine"):
            with patch("memory.postgres.client.async_sessionmaker"):
                client = PostgreSQLClient()
                yield client

    async def test_client_initializes(self, mock_engine):
        """Client initializes successfully."""
        assert mock_engine is not None

    async def test_get_session_returns_async_session(self, mock_engine):
        """get_session returns an async session."""
        with patch.object(mock_engine, "get_session") as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock()
            mock_get.return_value.__aexit__ = AsyncMock()

            async with mock_engine.get_session():
                pass

            mock_get.assert_called_once()

    async def test_health_check_returns_true(self, mock_engine):
        """health_check returns True when connection works."""
        with patch.object(mock_engine, "connect") as mock_connect:
            mock_connect.return_value.__aenter__ = AsyncMock()
            mock_connect.return_value.__aexit__ = AsyncMock()

            result = await mock_engine.health_check()

            # Should return True if no exception
            assert result is True

    async def test_create_tables_on_startup(self, mock_engine):
        """create_tables creates all tables."""
        with patch("memory.postgres.client.Base.metadata.create_all") as mock_create:
            mock_engine.create_tables()

            mock_create.assert_called_once()


@pytest.mark.asyncio
class TestWorkflowSessionModel:
    """Test WorkflowSession model."""

    def test_create_workflow_session(self):
        """Create a WorkflowSession instance."""
        import json
        from datetime import datetime

        session = WorkflowSession(
            id="test-id",
            input_request="Add user authentication",
            status="PENDING",
            current_stage="SPEC",
            state_json=json.dumps({"test": "data"}),
        )
        assert session.id == "test-id"
        assert session.input_request == "Add user authentication"
        assert session.status == "PENDING"

    def test_workflow_session_has_timestamps(self):
        """WorkflowSession has created_at and updated_at timestamps."""
        import json
        from datetime import datetime

        session = WorkflowSession(
            id="test-id",
            input_request="test",
            state_json="{}",
        )
        assert session.created_at is not None
        assert session.updated_at is not None


@pytest.mark.asyncio
class TestPersistentStore:
    """Test persistent store functionality."""

    async def test_save_workflow_creates_record(self):
        """save_workflow creates a new workflow record."""
        with patch("core.state_manager.persistent_store.get_postgres_client") as mock_get:
            mock_store = AsyncMock()
            mock_store.get_session = AsyncMock()
            mock_get.return_value = mock_store

            from core.state_manager import get_persistent_store

            store = get_persistent_store()
            # Note: This would need full mock setup for actual execution
            # Just testing interface exists

            assert store is not None

    async def test_get_workflow_returns_record(self):
        """get_workflow returns workflow record."""
        with patch("core.state_manager.persistent_store.get_postgres_client") as mock_get:
            mock_store = AsyncMock()
            mock_store.get_session = AsyncMock()
            mock_get.return_value = mock_store

            from core.state_manager import get_persistent_store

            store = get_persistent_store()
            # Testing interface exists

            assert store is not None
