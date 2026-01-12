"""Global exception classes for The Hive."""

from typing import Any, Optional


class HiveException(Exception):
    """Base exception for The Hive."""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        """Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class WorkflowException(HiveException):
    """Exception raised during workflow execution."""

    pass


class AgentException(HiveException):
    """Exception raised during agent execution."""

    pass


class SandboxException(HiveException):
    """Exception raised during sandbox execution."""

    pass


class MemoryException(HiveException):
    """Exception raised during memory operations."""

    pass


class ValidationException(HiveException):
    """Exception raised during input validation."""

    pass


class RateLimitException(HiveException):
    """Exception raised when rate limit is exceeded."""

    pass
