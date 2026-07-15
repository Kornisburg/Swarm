"""Sandbox lifecycle management for The Hive."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from .docker_runner import DockerSandboxRunner
from core.exceptions import SandboxException


class SandboxManager:
    """Manage sandbox execution sessions."""

    def __init__(self):
        """Initialize sandbox manager."""
        self.runner = DockerSandboxRunner()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        code: str,
        language: str = "python",
        timeout: int = 300,
        mem_limit: str = "512m",
        cpu_limit: float = 0.5,
    ) -> str:
        """Create and execute a sandbox session.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Timeout in seconds
            mem_limit: Memory limit
            cpu_limit: CPU limit (0.5 = half a CPU)

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        # Configure session
        session = {
            "session_id": session_id,
            "code": code,
            "language": language,
            "resource_limits": {
                "timeout_seconds": timeout,
                "memory_limit": mem_limit,
                "cpu_limit": cpu_limit,
                "network_enabled": False,
            },
            "created_at": datetime.utcnow(),
            "status": "CREATING",
        }

        self.active_sessions[session_id] = session

        # Execute
        try:
            session["status"] = "RUNNING"
            session["started_at"] = datetime.utcnow()

            result = self.runner.execute_code(
                code=code,
                language=language,
                timeout=timeout,
                mem_limit=mem_limit,
                cpu_quota=int(cpu_limit * 100000),
            )

            session.update(
                {
                    "status": "COMPLETED" if result["success"] else "FAILED",
                    "completed_at": datetime.utcnow(),
                    "exit_code": result["exit_code"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "container_id": result["container_id"],
                    "resource_usage": {
                        "duration_seconds": (
                            datetime.utcnow() - session["started_at"]
                        ).total_seconds()
                    },
                }
            )

        except SandboxException as e:
            session.update(
                {
                    "status": "FAILED",
                    "completed_at": datetime.utcnow(),
                    "error": str(e),
                    "stderr": str(e),
                }
            )

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details.

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        return self.active_sessions.get(session_id)

    def kill_session(self, session_id: str) -> bool:
        """Terminate a running session.

        Args:
            session_id: Session ID to kill

        Returns:
            True if successful
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        # Kill container if running
        if session.get("container_id"):
            self.runner.kill_container(session["container_id"])

        session["status"] = "TERMINATED"
        session["completed_at"] = datetime.utcnow()
        return True

    def health_check(self) -> bool:
        """Check sandbox system health.

        Returns:
            True if healthy
        """
        return self.runner.health_check()
