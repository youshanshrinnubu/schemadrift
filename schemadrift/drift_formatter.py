"""Formats DriftReport objects into human-readable or structured output."""

from __future__ import annotations

from enum import Enum
from typing import List

from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType


class OutputFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


_CHANGE_SYMBOLS = {
    ChangeType.COLUMN_ADDED: "+",
    ChangeType.COLUMN_REMOVED: "-",
    ChangeType.TYPE_CHANGED: "~",
    ChangeType.NULLABLE_CHANGED: "!",
}


def _format_change_text(change: DriftChange) -> str:
    symbol = _CHANGE_SYMBOLS.get(change.change_type, "?")
    parts = [f"  [{symbol}] {change.change_type.value}: column '{change.column_name}'"]
    if change.old_value is not None:
        parts.append(f"      before: {change.old_value}")
    if change.new_value is not None:
        parts.append(f"      after:  {change.new_value}")
    return "\n".join(parts)


def _format_change_markdown(change: DriftChange) -> str:
    symbol = _CHANGE_SYMBOLS.get(change.change_type, "?")
    line = f"| `{change.column_name}` | {change.change_type.value} |"
    if change.old_value is not None or change.new_value is not None:
        line += f" `{change.old_value}` → `{change.new_value}` |"
    else:
        line += " — |"
    return line


def format_report(report: DriftReport, fmt: OutputFormat = OutputFormat.TEXT) -> str:
    if fmt == OutputFormat.JSON:
        import json
        return json.dumps(report.to_dict(), indent=2)

    header_from = f"{report.source_name} @ v{report.from_version}"
    header_to = f"{report.source_name} @ v{report.to_version}"

    if fmt == OutputFormat.MARKDOWN:
        if not report.has_drift():
            return f"## Schema Diff: {header_from} → {header_to}\n\n_No changes detected._"
        lines = [
            f"## Schema Diff: {header_from} → {header_to}",
            "",
            "| Column | Change | Detail |",
            "|--------|--------|--------|",
        ]
        lines += [_format_change_markdown(c) for c in report.changes]
        return "\n".join(lines)

    # TEXT (default)
    if not report.has_drift():
        return f"No drift detected between {header_from} and {header_to}."
    lines = [
        f"Drift detected: {header_from} → {header_to}",
        f"  {len(report.changes)} change(s):",
    ]
    lines += [_format_change_text(c) for c in report.changes]
    return "\n".join(lines)
