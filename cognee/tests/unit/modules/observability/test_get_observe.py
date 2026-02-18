"""Unit tests for cognee.modules.observability.get_observe."""

import sys
from unittest.mock import MagicMock, patch

from cognee.modules.observability.get_observe import get_observe
from cognee.modules.observability.observers import Observer


def _fake_langfuse_decorators_module():
    """Fake langfuse.decorators so in-function import succeeds when langfuse not installed."""
    mod = type(sys)("langfuse.decorators")
    mod.observe = lambda *a, **k: (
        a[0] if len(a) == 1 and callable(a[0]) and not k else (lambda f: f)
    )
    return mod


def test_get_observe_never_returns_none():
    """get_observe() must never return None for any Observer value."""
    fake_decorators = _fake_langfuse_decorators_module()
    modules_patch = {"langfuse": MagicMock(), "langfuse.decorators": fake_decorators}

    for observer in Observer:
        with (
            patch("cognee.modules.observability.get_observe.get_base_config") as mock_get_config,
            patch.dict(sys.modules, modules_patch),
        ):
            mock_config = MagicMock()
            mock_config.monitoring_tool = observer
            mock_get_config.return_value = mock_config

            observe = get_observe()

        assert observe is not None, f"get_observe() returned None for {observer}"
        assert callable(observe), f"get_observe() returned non-callable for {observer}"


def test_get_observe_no_op_direct_decorator():
    """No-op observe works as @observe (direct decoration)."""
    with patch("cognee.modules.observability.get_observe.get_base_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.monitoring_tool = Observer.NONE
        mock_get_config.return_value = mock_config

        observe = get_observe()

    @observe
    def my_func() -> str:
        return "ok"

    assert my_func() == "ok"


def test_get_observe_no_op_parameterized_decorator():
    """No-op observe works as @observe(as_type='generation')."""
    with patch("cognee.modules.observability.get_observe.get_base_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.monitoring_tool = Observer.NONE
        mock_get_config.return_value = mock_config

        observe = get_observe()

    @observe(as_type="generation")
    def my_func() -> str:
        return "ok"

    assert my_func() == "ok"


def test_get_observe_unhandled_observer_returns_no_op():
    """Unhandled observers (e.g. LLMLITE, LANGSMITH) return a valid no-op decorator."""
    with patch("cognee.modules.observability.get_observe.get_base_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.monitoring_tool = Observer.LLMLITE
        mock_get_config.return_value = mock_config

        observe = get_observe()

    assert observe is not None
    assert callable(observe)

    @observe
    def my_func() -> str:
        return "llmlite"

    assert my_func() == "llmlite"


def test_get_observe_langfuse_returns_langfuse_observe():
    """When LANGFUSE is set, get_observe returns langfuse's observe decorator."""

    def langfuse_observe(*args: object, **kwargs: object) -> object:
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return lambda f: f

    # Inject a fake langfuse.decorators so the in-function import succeeds
    langfuse_decorators = type(sys)("langfuse.decorators")
    langfuse_decorators.observe = langfuse_observe

    with (
        patch("cognee.modules.observability.get_observe.get_base_config") as mock_get_config,
        patch.dict(
            sys.modules,
            {"langfuse": MagicMock(), "langfuse.decorators": langfuse_decorators},
        ),
    ):
        mock_config = MagicMock()
        mock_config.monitoring_tool = Observer.LANGFUSE
        mock_get_config.return_value = mock_config

        observe = get_observe()

    assert observe is langfuse_observe

    @observe
    def my_func() -> str:
        return "langfuse"

    assert my_func() == "langfuse"
