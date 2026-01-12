"""Structured JSON logging with request IDs for The Hive."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional
from contextvars import ContextVar

# Context variable for request ID
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class HiveLogger:
    """Structured logger for The Hive."""

    def __init__(self, name: str):
        """Initialize logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def with_request_id(self, request_id: str) -> "HiveLogger":
        """Set request ID context.

        Args:
            request_id: Request ID

        Returns:
            Self for chaining
        """
        request_id_ctx.set(request_id)
        return self

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message.

        Args:
            msg: Log message
            **kwargs: Additional fields
        """
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message.

        Args:
            msg: Log message
            **kwargs: Additional fields
        """
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message.

        Args:
            msg: Log message
            **kwargs: Additional fields
        """
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message.

        Args:
            msg: Log message
            **kwargs: Additional fields
        """
        self._log(logging.ERROR, msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        """Internal log method.

        Args:
            level: Log level
            msg: Log message
            **kwargs: Additional fields
        """
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, msg, extra=extra)


def get_logger(name: str) -> HiveLogger:
    """Get or create a logger.

    Args:
        name: Logger name

    Returns:
        HiveLogger instance
    """
    return HiveLogger(name)


def generate_request_id() -> str:
    """Generate a new request ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())
