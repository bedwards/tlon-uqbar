"""Tests for bandmix_cli.formatters."""

from __future__ import annotations

import json
from unittest.mock import patch

from pydantic import BaseModel

from bandmix_cli.formatters import (
    auto_format,
    format_json,
    format_output,
    format_raw,
    format_table,
    format_text,
)


class SampleModel(BaseModel):
    name: str
    age: int
    instruments: list[str] = []


# --- format_table ---


class TestFormatTable:
    def test_single_dict(self):
        result = format_table({"name": "Jim", "city": "Austin"})
        assert "name" in result
        assert "Jim" in result
        assert "city" in result
        assert "Austin" in result

    def test_list_of_dicts(self):
        data = [
            {"name": "Jim", "city": "Austin"},
            {"name": "Bob", "city": "Dallas"},
        ]
        result = format_table(data)
        lines = result.split("\n")
        # header, separator, 2 data rows
        assert len(lines) == 4
        assert "name" in lines[0]
        assert "city" in lines[0]
        assert "---" in lines[1] or "---" in lines[1]
        assert "Jim" in lines[2]
        assert "Bob" in lines[3]

    def test_pydantic_model(self):
        model = SampleModel(name="Jim", age=30, instruments=["Guitar", "Drums"])
        result = format_table(model)
        assert "name" in result
        assert "Jim" in result
        assert "Guitar, Drums" in result

    def test_list_of_models(self):
        models = [
            SampleModel(name="Jim", age=30),
            SampleModel(name="Bob", age=25),
        ]
        result = format_table(models)
        assert "Jim" in result
        assert "Bob" in result

    def test_empty_list(self):
        assert format_table([]) == ""

    def test_empty_dict(self):
        assert format_table({}) == ""

    def test_none_values(self):
        result = format_table({"name": "Jim", "bio": None})
        assert "name" in result
        assert "Jim" in result

    def test_bool_values(self):
        result = format_table({"active": True, "hidden": False})
        assert "True" in result
        assert "False" in result

    def test_single_item_list_renders_horizontal(self):
        """A single-item list should render as a horizontal table, not vertical."""
        data = [{"name": "Jim", "city": "Austin"}]
        result = format_table(data)
        lines = result.split("\n")
        # header, separator, 1 data row
        assert len(lines) == 3


# --- format_json ---


class TestFormatJson:
    def test_dict_tty(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            result = format_json({"name": "Jim"})
        parsed = json.loads(result)
        assert parsed == {"name": "Jim"}
        # Pretty-printed has newlines
        assert "\n" in result

    def test_dict_pipe(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=False):
            result = format_json({"name": "Jim"})
        parsed = json.loads(result)
        assert parsed == {"name": "Jim"}
        # Compact has no spaces after separators
        assert "\n" not in result

    def test_list_of_dicts(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            result = format_json([{"a": 1}, {"a": 2}])
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_pydantic_model(self):
        model = SampleModel(name="Jim", age=30, instruments=["Guitar"])
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            result = format_json(model)
        parsed = json.loads(result)
        assert parsed["name"] == "Jim"
        assert parsed["instruments"] == ["Guitar"]

    def test_single_dict_not_wrapped_in_list(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            result = format_json({"x": 1})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


# --- format_text ---


class TestFormatText:
    def test_single_dict(self):
        result = format_text({"name": "Jim", "city": "Austin"})
        assert "name: Jim" in result
        assert "city: Austin" in result

    def test_list_of_dicts(self):
        data = [{"name": "Jim"}, {"name": "Bob"}]
        result = format_text(data)
        assert "name: Jim" in result
        assert "name: Bob" in result
        # Separated by blank line
        assert "\n\n" in result

    def test_pydantic_model(self):
        model = SampleModel(name="Jim", age=30, instruments=["Guitar", "Bass"])
        result = format_text(model)
        assert "name: Jim" in result
        assert "instruments: Guitar, Bass" in result

    def test_empty_list(self):
        assert format_text([]) == ""


# --- format_raw ---


class TestFormatRaw:
    def test_passthrough(self):
        html = "<html><body>Hello</body></html>"
        assert format_raw(html) == html

    def test_non_string(self):
        assert format_raw(42) == "42"


# --- format_output dispatcher ---


class TestFormatOutput:
    def test_dispatches_table(self):
        result = format_output({"name": "Jim"}, fmt="table")
        assert "name" in result
        assert "Jim" in result

    def test_dispatches_json(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            result = format_output({"name": "Jim"}, fmt="json")
        parsed = json.loads(result)
        assert parsed["name"] == "Jim"

    def test_dispatches_text(self):
        result = format_output({"name": "Jim"}, fmt="text")
        assert "name: Jim" in result

    def test_dispatches_raw(self):
        result = format_output("<html>hi</html>", fmt="raw")
        assert result == "<html>hi</html>"

    def test_unknown_format_raises(self):
        try:
            format_output({}, fmt="xml")
            raise AssertionError("Expected ValueError")
        except ValueError as e:
            assert "xml" in str(e)


# --- auto_format ---


class TestAutoFormat:
    def test_tty_returns_table(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=True):
            assert auto_format() == "table"

    def test_pipe_returns_json(self):
        with patch("bandmix_cli.formatters.is_tty", return_value=False):
            assert auto_format() == "json"
