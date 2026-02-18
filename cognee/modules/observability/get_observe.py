from typing import Any, Callable

from cognee.base_config import get_base_config
from .observers import Observer


def _no_op_observe() -> Callable[..., Any]:
    """Return a no-op decorator compatible with @observe / @observe(...)."""

    def no_op_decorator(*args: Any, **kwargs: Any) -> Any:
        if len(args) == 1 and callable(args[0]) and not kwargs:
            # Direct decoration: @observe
            return args[0]

        # Parameterized decoration: @observe(as_type="generation")
        def decorator(func: Callable[..., Any]) -> Any:
            return func

        return decorator

    return no_op_decorator


def get_observe() -> Any:
    monitoring = get_base_config().monitoring_tool

    if monitoring == Observer.LANGFUSE:
        from langfuse.decorators import observe

        return observe
    # NONE, LLMLITE, LANGSMITH, or any other observer: return no-op so we never return None
    return _no_op_observe()
