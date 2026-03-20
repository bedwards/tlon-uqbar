"""Output formatters for bandmix-cli (table, JSON, text, raw)."""

from __future__ import annotations

import json
import sys
from typing import Any


def _to_dicts(data: Any) -> list[dict[str, Any]]:
    """Normalize data to a list of dicts.

    Supports Pydantic models, dicts, and lists of either.
    """
    if isinstance(data, list):
        return [_single_to_dict(item) for item in data]
    return [_single_to_dict(data)]


def _single_to_dict(item: Any) -> dict[str, Any]:
    """Convert a single item to a dict."""
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if isinstance(item, dict):
        return item
    raise TypeError(f"Unsupported data type: {type(item).__name__}")


def format_output(data: Any, fmt: str = "table") -> str:
    """Dispatch to the appropriate formatter.

    Parameters
    ----------
    data:
        A dict, Pydantic model, or list of either.
    fmt:
        One of "table", "json", "text", "raw".

    Returns
    -------
    str
        Formatted output string.
    """
    formatters = {
        "table": format_table,
        "json": format_json,
        "text": format_text,
        "raw": format_raw,
    }
    formatter = formatters.get(fmt)
    if formatter is None:
        raise ValueError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(formatters)}"
        )
    return formatter(data)


def format_table(data: Any) -> str:
    """Format data as an aligned table.

    Single dicts render as a two-column key/value table.
    Lists render with column headers derived from dict keys.
    """
    rows = _to_dicts(data)
    if not rows:
        return ""

    # For a single dict, render vertical key: value layout
    if len(rows) == 1 and not isinstance(data, list):
        return _vertical_table(rows[0])

    return _horizontal_table(rows)


def _vertical_table(d: dict[str, Any]) -> str:
    """Render a single dict as a vertical two-column table."""
    if not d:
        return ""
    key_width = max(len(str(k)) for k in d)
    lines = []
    for key, value in d.items():
        lines.append(f"{str(key):<{key_width}}  {_cell(value)}")
    return "\n".join(lines)


def _horizontal_table(rows: list[dict[str, Any]]) -> str:
    """Render a list of dicts as a horizontal table with headers."""
    if not rows:
        return ""

    # Collect all keys preserving order of first appearance
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                columns.append(key)
                seen.add(key)

    # Calculate column widths
    widths: dict[str, int] = {}
    for col in columns:
        header_len = len(col)
        max_val = max((len(_cell(row.get(col, ""))) for row in rows), default=0)
        widths[col] = max(header_len, max_val)

    # Build header
    header = "  ".join(f"{col:<{widths[col]}}" for col in columns)
    separator = "  ".join("-" * widths[col] for col in columns)

    # Build rows
    lines = [header, separator]
    for row in rows:
        line = "  ".join(f"{_cell(row.get(col, '')):<{widths[col]}}" for col in columns)
        lines.append(line)

    return "\n".join(lines)


def _cell(value: Any) -> str:
    """Convert a value to a cell string for table display."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return ""
    return str(value)


def format_json(data: Any) -> str:
    """Format data as JSON.

    Pretty-prints with indentation when stdout is a TTY,
    compact output otherwise (for piping).
    """
    rows = _to_dicts(data)

    # Unwrap single-item list when input was not a list
    if len(rows) == 1 and not isinstance(data, list):
        payload = rows[0]
    else:
        payload = rows

    if is_tty():
        return json.dumps(payload, indent=2, default=str)
    return json.dumps(payload, separators=(",", ":"), default=str)


def format_text(data: Any) -> str:
    """Format data as plain key: value text.

    Multiple items are separated by a blank line.
    """
    rows = _to_dicts(data)
    if not rows:
        return ""

    blocks: list[str] = []
    for row in rows:
        lines = []
        for key, value in row.items():
            lines.append(f"{key}: {_cell(value)}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_raw(html: Any) -> str:
    """Pass through raw HTML unchanged."""
    return str(html)


def is_tty() -> bool:
    """Return True if stdout is connected to a terminal."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def auto_format() -> str:
    """Select a default format based on whether stdout is a TTY."""
    return "table" if is_tty() else "json"
