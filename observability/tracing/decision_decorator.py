"""Decision tracking decorator for observability."""

import functools
import inspect
from typing import Any, Callable, Optional

from ..exporters.langsmith import get_langsmith_exporter


def track_decision(
    decision_type: str,
    confidence_threshold: float = 0.0,
    track_input: bool = True,
    track_output: bool = True,
) -> Callable:
    """Decorator to track agent decisions.

    Args:
        decision_type: Type of decision being made
        confidence_threshold: Minimum confidence to record (0-1)
        track_input: Whether to track function inputs
        track_output: Whether to track function outputs

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        """Apply decision tracking to function."""

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrap async function for decision tracking."""
            return await _track_decision(
                func, args, kwargs, decision_type, confidence_threshold, track_input, track_output, True
            )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrap sync function for decision tracking."""
            return _track_decision(
                func, args, kwargs, decision_type, confidence_threshold, track_input, track_output, False
            )

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _track_decision(
    func: Callable,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    decision_type: str,
    confidence_threshold: float,
    track_input: bool,
    track_output: bool,
    is_async: bool,
) -> Any:
    """Track a decision and execute the function.

    Args:
        func: Function to execute
        args: Function positional arguments
        kwargs: Function keyword arguments
        decision_type: Type of decision
        confidence_threshold: Minimum confidence
        track_input: Whether to track inputs
        track_output: Whether to track outputs
        is_async: Whether function is async

    Returns:
        Function result
    """
    # Extract agent type from function's class if available
    agent_type = "UNKNOWN"
    if args and hasattr(args[0], "__class__"):
        agent_type = args[0].__class__.__name__.replace("Agent", "").upper()

    # Track the decision
    decision_data = {
        "decision_type": decision_type,
        "agent_type": agent_type,
        "confidence": 1.0,  # Default confidence
        "rationale": f"Execution of {func.__name__}",
    }

    if track_input:
        decision_data["input"] = {
            "args": _serialize_args(args[1:], kwargs),  # Skip self
            "function": func.__name__,
        }

    # Execute function
    if is_async:
        import asyncio
        result = asyncio.run(func(*args, **kwargs))
    else:
        result = func(*args, **kwargs)

    if track_output:
        decision_data["output"] = _serialize_output(result)

    # Export to LangSmith
    try:
        exporter = get_langsmith_exporter()
        exporter.track_decision(decision_data)
    except Exception:
        # Don't break the function if tracking fails
        pass

    return result


def _serialize_args(args: tuple, kwargs: dict) -> dict[str, Any]:
    """Serialize function arguments for tracking.

    Args:
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Serialized arguments
    """
    serialized = {"args_count": len(args)}
    if args:
        serialized["args"] = [_safe_repr(arg) for arg in args[:3]]  # Limit to first 3
    if kwargs:
        serialized["kwargs"] = {k: _safe_repr(v) for k, v in list(kwargs.items())[:3]}  # Limit to first 3
    return serialized


def _serialize_output(output: Any) -> dict[str, Any]:
    """Serialize function output for tracking.

    Args:
        output: Function output

    Returns:
        Serialized output
    """
    if output is None:
        return {"type": "None"}
    elif isinstance(output, dict):
        return {
            "type": "dict",
            "keys": list(output.keys())[:5],  # Limit to first 5 keys
        }
    elif isinstance(output, (list, tuple)):
        return {
            "type": "list" if isinstance(output, list) else "tuple",
            "length": len(output),
        }
    else:
        return {
            "type": type(output).__name__,
            "repr": _safe_repr(output),
        }


def _safe_repr(obj: Any) -> str:
    """Get safe representation of object.

    Args:
        obj: Object to represent

    Returns:
        Safe string representation
    """
    try:
        repr_str = repr(obj)
        # Limit representation length
        if len(repr_str) > 200:
            return repr_str[:200] + "..."
        return repr_str
    except Exception:
        return f"<{type(obj).__name__} object>"
