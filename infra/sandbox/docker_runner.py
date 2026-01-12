"""Docker sandbox runner for secure code execution."""

import docker
from docker.errors import DockerException
from typing import Optional, Dict, Any
import uuid

from ...core.exceptions import SandboxException
from ...core.config import get_settings


class DockerSandboxRunner:
    """Run code in isolated Docker containers."""

    def __init__(self):
        """Initialize Docker sandbox runner."""
        try:
            self.client = docker.from_env()
            self.default_image = "python:3.11-slim"
        except Exception as e:
            raise SandboxException(f"Failed to initialize Docker: {str(e)}")

    def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: int = 300,
        mem_limit: str = "512m",
        cpu_quota: int = 50000,
    ) -> Dict[str, Any]:
        """Execute code in isolated sandbox.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Execution timeout in seconds
            mem_limit: Memory limit (e.g., "512m")
            cpu_quota: CPU quota (100000 = 1 CPU)

        Returns:
            Execution result

        Raises:
            SandboxException: If execution fails
        """
        container_id = None

        try:
            # Prepare code for execution
            if language == "python":
                command = f'python3 -c "{code.replace(chr(34), chr(92) + chr(34))}"'
            else:
                raise SandboxException(f"Unsupported language: {language}")

            # Create container
            container = self.client.containers.run(
                image=self.default_image,
                command=["sh", "-c", command],
                network_mode="none",  # No network access
                mem_limit=mem_limit,
                cpu_quota=cpu_quota,
                read_only=True,  # Read-only filesystem
                tmpfs={"/tmp": "size=100m"},  # Writable /tmp only
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                detach=True,
                remove=False,
            )

            container_id = container.id

            # Wait for completion with timeout
            result = container.wait(timeout=timeout)

            # Get logs
            stdout = container.logs(stdout=True).decode("utf-8")
            stderr = container.logs(stderr=True).decode("utf-8")

            # Cleanup
            container.remove(force=True)

            return {
                "container_id": container_id,
                "exit_code": result["StatusCode"],
                "stdout": stdout,
                "stderr": stderr,
                "success": result["StatusCode"] == 0,
            }

        except DockerException as e:
            if container_id:
                try:
                    container = self.client.containers.get(container_id)
                    container.remove(force=True)
                except:
                    pass
            raise SandboxException(f"Docker execution failed: {str(e)}")

    def kill_container(self, container_id: str) -> None:
        """Immediately terminate a container.

        Args:
            container_id: Container ID to kill
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
        except Exception:
            pass  # Already removed or doesn't exist

    def health_check(self) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker is accessible
        """
        try:
            self.client.ping()
            return True
        except Exception:
            return False
