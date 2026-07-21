"""Decision tracking decorator for observability."""

import asyncio
import functools
from collections.abc import Callable
from typing import Any

from .decision_tracker import DecisionTracker


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
            result = await func(*args, **kwargs)
            _track_decision_sync(
                func, args, kwargs, decision_type, confidence_threshold, track_input, track_output, result
            )
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrap sync function for decision tracking."""
            result = func(*args, **kwargs)
            _track_decision_sync(
                func, args, kwargs, decision_type, confidence_threshold, track_input, track_output, result
            )
            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _track_decision_sync(
    func: Callable,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    decision_type: str,
    confidence_threshold: float,
    track_input: bool,
    track_output: bool,
    result: Any,
) -> None:
    """Record decision tracking metadata after function execution.

    Args:
        func: Function that executed
        args: Function positional arguments
        kwargs: Function keyword arguments
        decision_type: Type of decision
        confidence_threshold: Minimum confidence
        track_input: Whether to track inputs
        track_output: Whether to track outputs
        result: Function result
    """
    tracker = _get_tracker()

    agent_type = "UNKNOWN"
    workflow_id = None
    input_context = {}
    if args and hasattr(args[0], "__class__"):
        agent_type = args[0].__class__.__name__.replace("Agent", "").upper()

    if track_input:
        input_context = _serialize_args(args[1:], kwargs)

    if args and len(args) > 1 and hasattr(args[1], "workflow_id"):
        workflow_id = args[1].workflow_id

    output_decision = {}
    if track_output:
        output_decision = _serialize_output(result)

    try:
        tracker.record_decision(
            agent_type=agent_type,
            decision_type=decision_type,
            input_context=input_context,
            output_decision=output_decision,
            confidence=1.0,
            rationale=f"Execution of {func.__name__}",
            workflow_id=workflow_id,
        )
    except Exception:
        pass


def _get_tracker() -> DecisionTracker:
    """Get or create the global decision tracker."""
    if not hasattr(_get_tracker, "_tracker"):
        _get_tracker._tracker = DecisionTracker()
    return _get_tracker._tracker


def get_decision_tracker() -> DecisionTracker:
    """Public accessor for the decision tracker singleton.

    Returns:
        Global DecisionTracker instance
    """
    return _get_tracker()


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
