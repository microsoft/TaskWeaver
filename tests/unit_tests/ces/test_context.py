"""Unit tests for ExecutorPluginContext, focusing on extract_visible_variables."""

import types
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from taskweaver.ces.runtime.context import ExecutorPluginContext


def _has_numpy() -> bool:
    """Check if numpy is available."""
    try:
        import numpy  # noqa: F401

        return True
    except ImportError:
        return False


class TestExtractVisibleVariables:
    """Tests for the extract_visible_variables method."""

    @pytest.fixture()
    def context(self) -> ExecutorPluginContext:
        """Create an ExecutorPluginContext with a mocked executor."""
        mock_executor = MagicMock()
        mock_executor.session_var = {}
        return ExecutorPluginContext(mock_executor)

    def test_string_variable_no_extra_quotes(self, context: ExecutorPluginContext) -> None:
        """Test that string variables are rendered without extra quotes."""
        local_ns: Dict[str, Any] = {"filename": "data.csv"}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, rendered = result[0]
        assert name == "filename"
        assert rendered == "data.csv"
        assert rendered != "'data.csv'"

    def test_string_with_spaces(self, context: ExecutorPluginContext) -> None:
        """Test string with spaces renders correctly."""
        local_ns: Dict[str, Any] = {"path": "/path/to/my file.txt"}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "/path/to/my file.txt"

    def test_empty_string(self, context: ExecutorPluginContext) -> None:
        """Test empty string renders as empty."""
        local_ns: Dict[str, Any] = {"empty": ""}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == ""

    def test_string_with_quotes_inside(self, context: ExecutorPluginContext) -> None:
        """Test string containing quotes renders correctly."""
        local_ns: Dict[str, Any] = {"quoted": "He said 'hello'"}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "He said 'hello'"

    def test_multiline_string(self, context: ExecutorPluginContext) -> None:
        """Test multiline string renders with actual newlines."""
        local_ns: Dict[str, Any] = {"text": "line1\nline2"}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "line1\nline2"
        assert "\\n" not in rendered

    def test_integer_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test integer variables use repr (same result as str for int)."""
        local_ns: Dict[str, Any] = {"count": 42}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "42"

    def test_float_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test float variables use repr."""
        local_ns: Dict[str, Any] = {"pi": 3.14159}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "3.14159"

    def test_list_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test list variables use repr to show brackets."""
        local_ns: Dict[str, Any] = {"items": [1, 2, 3]}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "[1, 2, 3]"

    def test_dict_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test dict variables use repr to show braces."""
        local_ns: Dict[str, Any] = {"data": {"key": "value"}}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "{'key': 'value'}"

    def test_boolean_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test boolean variables use repr."""
        local_ns: Dict[str, Any] = {"flag": True}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "True"

    def test_none_uses_repr(self, context: ExecutorPluginContext) -> None:
        """Test None uses repr."""
        local_ns: Dict[str, Any] = {"nothing": None}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "None"

    def test_ignores_private_variables(self, context: ExecutorPluginContext) -> None:
        """Test that variables starting with underscore are ignored."""
        local_ns: Dict[str, Any] = {
            "_private": "hidden",
            "__dunder": "also hidden",
            "public": "visible",
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, _ = result[0]
        assert name == "public"

    def test_ignores_builtin_names(self, context: ExecutorPluginContext) -> None:
        """Test that builtin IPython names are ignored."""
        local_ns: Dict[str, Any] = {
            "In": [],
            "Out": {},
            "__builtins__": {},
            "user_var": "visible",
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, _ = result[0]
        assert name == "user_var"

    def test_ignores_common_imports(self, context: ExecutorPluginContext) -> None:
        """Test that common library aliases (pd, np, plt) are ignored."""
        local_ns: Dict[str, Any] = {
            "pd": MagicMock(),
            "np": MagicMock(),
            "plt": MagicMock(),
            "my_data": "visible",
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, _ = result[0]
        assert name == "my_data"

    def test_ignores_modules(self, context: ExecutorPluginContext) -> None:
        """Test that module objects are ignored."""
        local_ns: Dict[str, Any] = {
            "os_module": types.ModuleType("os"),
            "user_var": "visible",
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, _ = result[0]
        assert name == "user_var"

    def test_ignores_functions(self, context: ExecutorPluginContext) -> None:
        """Test that function objects are ignored."""

        def my_func() -> None:
            pass

        local_ns: Dict[str, Any] = {
            "my_func": my_func,
            "user_var": "visible",
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        name, _ = result[0]
        assert name == "user_var"

    def test_truncates_long_values(self, context: ExecutorPluginContext) -> None:
        """Test that values longer than 500 chars are truncated."""
        long_string = "x" * 1000
        local_ns: Dict[str, Any] = {"long": long_string}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert len(rendered) == 500
        assert rendered == "x" * 500

    def test_multiple_variables(self, context: ExecutorPluginContext) -> None:
        """Test extracting multiple variables of different types."""
        local_ns: Dict[str, Any] = {
            "name": "Alice",
            "age": 30,
            "scores": [85, 90, 78],
        }
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 3
        result_dict = dict(result)
        assert result_dict["name"] == "Alice"
        assert result_dict["age"] == "30"
        assert result_dict["scores"] == "[85, 90, 78]"

    def test_updates_latest_variables(self, context: ExecutorPluginContext) -> None:
        """Test that latest_variables is updated after extraction."""
        local_ns: Dict[str, Any] = {"var": "value"}
        result = context.extract_visible_variables(local_ns)

        assert context.latest_variables == result

    def test_unrepresentable_value(self, context: ExecutorPluginContext) -> None:
        """Test handling of values that raise on repr()."""

        class BadRepr:
            def __repr__(self) -> str:
                raise ValueError("Cannot repr")

        local_ns: Dict[str, Any] = {"bad": BadRepr()}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert rendered == "<unrepresentable>"


class TestExtractVisibleVariablesWithNumpy:
    """Tests for extract_visible_variables with numpy arrays."""

    @pytest.fixture()
    def context(self) -> ExecutorPluginContext:
        """Create an ExecutorPluginContext with a mocked executor."""
        mock_executor = MagicMock()
        mock_executor.session_var = {}
        return ExecutorPluginContext(mock_executor)

    @pytest.mark.skipif(
        not _has_numpy(),
        reason="numpy not installed",
    )
    def test_numpy_array_rendering(self, context: ExecutorPluginContext) -> None:
        """Test numpy array is rendered with shape and dtype info."""
        import numpy as np

        local_ns: Dict[str, Any] = {"arr": np.array([1, 2, 3])}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert "ndarray" in rendered
        assert "shape=(3,)" in rendered
        assert "dtype=int" in rendered

    @pytest.mark.skipif(
        not _has_numpy(),
        reason="numpy not installed",
    )
    def test_numpy_2d_array(self, context: ExecutorPluginContext) -> None:
        """Test 2D numpy array rendering."""
        import numpy as np

        local_ns: Dict[str, Any] = {"matrix": np.array([[1, 2], [3, 4]])}
        result = context.extract_visible_variables(local_ns)

        assert len(result) == 1
        _, rendered = result[0]
        assert "shape=(2, 2)" in rendered
