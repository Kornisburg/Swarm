"""Contract tests for sandbox execution."""

import pytest
from unittest.mock import AsyncMock, patch

from infra.sandbox.docker_runner import DockerSandboxRunner
from infra.sandbox.manager import SandboxManager


@pytest.mark.asyncio
class TestDockerSandboxRunner:
    """Test Docker sandbox runner contract."""

    async def test_runner_initializes_with_config(self):
        """Runner initializes with Docker configuration."""
        with patch("docker.DockerClient"):
            runner = DockerSandboxRunner()
            assert runner is not None

    async def test_run_code_returns_result(self):
        """Code execution returns result."""
        with patch("docker.DockerClient") as mock_docker:
            mock_container = AsyncMock()
            mock_container.logs.return_value = b"output"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_docker.return_value.containers.create.return_value = mock_container

            runner = DockerSandboxRunner()
            result = await runner.run_code("print('hello')", "python")

            assert result["exit_code"] == 0
            assert "stdout" in result

    async def test_run_code_enforces_timeout(self):
        """Code execution enforces timeout."""
        with patch("docker.DockerClient") as mock_docker:
            mock_container = AsyncMock()
            mock_container.logs.return_value = b""
            mock_container.wait.return_value = {"StatusCode": 124}  # Timeout
            mock_docker.return_value.containers.create.return_value = mock_container

            runner = DockerSandboxRunner()
            result = await runner.run_code("while True: pass", "python", timeout=1)

            assert result["exit_code"] == 124
            assert "timeout" in result.get("error", "").lower()

    async def test_run_code_isolates_network(self):
        """Code execution isolates network access."""
        with patch("docker.DockerClient") as mock_docker:
            create_kwargs = {}

            def capture_create(**kwargs):
                create_kwargs.update(kwargs)
                return AsyncMock()

            mock_docker.return_value.containers.create.side_effect = capture_create

            runner = DockerSandboxRunner()
            await runner.run_code("import requests", "python")

            # Check that network mode is set to none
            assert create_kwargs.get("network") == "none" or create_kwargs.get(
                "network_mode"
            ) == "none"

    async def test_run_code_enforces_memory_limit(self):
        """Code execution enforces memory limits."""
        with patch("docker.DockerClient") as mock_docker:
            create_kwargs = {}

            def capture_create(**kwargs):
                create_kwargs.update(kwargs)
                return AsyncMock()

            mock_docker.return_value.containers.create.side_effect = capture_create

            runner = DockerSandboxRunner()
            await runner.run_code("x = 'a' * 1000000", "python")

            # Check that mem_limit is set
            assert "mem_limit" in create_kwargs

    async def test_kill_switch_terminates_container(self):
        """Kill switch immediately terminates container."""
        with patch("docker.DockerClient") as mock_docker:
            mock_container = AsyncMock()
            mock_docker.return_value.containers.get.return_value = mock_container

            runner = DockerSandboxRunner()
            await runner.kill("test-container-id")

            mock_container.stop.assert_called_once()
            mock_container.remove.assert_called_once()


@pytest.mark.asyncio
class TestSandboxManager:
    """Test sandbox manager contract."""

    async def test_manager_creates_sandbox_session(self):
        """Manager creates a sandbox session."""
        with patch("infra.sandbox.manager.DockerSandboxRunner"):
            manager = SandboxManager()
            session = await manager.create_session("workflow-123", "python")

            assert session["workflow_id"] == "workflow-123"
            assert "session_id" in session

    async def test_manager_executes_code_in_session(self):
        """Manager executes code within a session."""
        with patch("infra.sandbox.manager.DockerSandboxRunner") as mock_runner:
            mock_runner.return_value.run_code = AsyncMock(
                return_value={"exit_code": 0, "stdout": "result"}
            )

            manager = SandboxManager()
            result = await manager.execute("session-123", "print('test')", "python")

            assert result["exit_code"] == 0
            assert "stdout" in result

    async def test_manager_captures_stdout_stderr(self):
        """Manager captures stdout and stderr from execution."""
        with patch("infra.sandbox.manager.DockerSandboxRunner") as mock_runner:
            mock_runner.return_value.run_code = AsyncMock(
                return_value={"exit_code": 0, "stdout": "output", "stderr": "error"}
            )

            manager = SandboxManager()
            result = await manager.execute("session-123", "code", "python")

            assert result["stdout"] == "output"
            assert result["stderr"] == "error"

    async def test_manager_enforces_timeout(self):
        """Manager enforces execution timeout."""
        with patch("infra.sandbox.manager.DockerSandboxRunner") as mock_runner:
            mock_runner.return_value.run_code = AsyncMock(
                return_value={"exit_code": 124, "error": "timeout"}
            )

            manager = SandboxManager()
            result = await manager.execute("session-123", "while True", "python")

            assert result["exit_code"] == 124

    async def test_manager_cleans_up_session(self):
        """Manager cleans up session resources."""
        with patch("infra.sandbox.manager.DockerSandboxRunner"):
            manager = SandboxManager()
            await manager.cleanup("session-123")

            # Should not raise exception
            assert True

    async def test_manager_health_check(self):
        """Manager reports health status."""
        with patch("infra.sandbox.manager.DockerSandboxRunner"):
            manager = SandboxManager()
            health = await manager.health_check()

            assert "healthy" in health or "status" in health
