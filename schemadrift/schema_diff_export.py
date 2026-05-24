"""Exports drift timelines and changelogs to structured formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from enum import Enum
from typing import List

from schemadrift.schema_changelog import Changelog, ChangelogEntry
from schemadrift.schema_diff_timeline import DriftTimeline, TimelineEntry


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


def _timeline_entry_to_row(entry: TimelineEntry) -> dict:
    return {
        "version": entry.version,
        "has_drift": entry.has_drift,
        "added": entry.added,
        "removed": entry.removed,
        "type_changed": entry.type_changed,
        "nullable_changed": entry.nullable_changed,
    }


def export_timeline(timeline: DriftTimeline, fmt: ExportFormat) -> str:
    entries = timeline.entries
    if fmt == ExportFormat.JSON:
        return json.dumps([e.to_dict() for e in entries], indent=2)

    if fmt == ExportFormat.CSV:
        buf = io.StringIO()
        fields = ["version", "has_drift", "added", "removed", "type_changed", "nullable_changed"]
        writer = csv.DictWriter(buf, fieldnames=fields)
        writer.writeheader()
        for e in entries:
            writer.writerow(_timeline_entry_to_row(e))
        return buf.getvalue()

    if fmt == ExportFormat.MARKDOWN:
        lines = ["| Version | Drift | Added | Removed | Type Changed | Nullable Changed |",
                 "|---------|-------|-------|---------|--------------|------------------|"
                 ]
        for e in entries:
            lines.append(
                f"| {e.version} | {'yes' if e.has_drift else 'no'} "
                f"| {e.added} | {e.removed} | {e.type_changed} | {e.nullable_changed} |"
            )
        return "\n".join(lines)

    raise ValueError(f"Unsupported format: {fmt}")


def export_changelog(changelog: Changelog, fmt: ExportFormat) -> str:
    entries: List[ChangelogEntry] = changelog.entries
    if fmt == ExportFormat.JSON:
        return json.dumps([e.to_dict() for e in entries], indent=2)

    if fmt == ExportFormat.CSV:
        buf = io.StringIO()
        fields = ["version", "change_type", "column", "detail"]
        writer = csv.DictWriter(buf, fieldnames=fields)
        writer.writeheader()
        for e in entries:
            writer.writerow({"version": e.version, "change_type": e.change_type,
                             "column": e.column, "detail": e.detail or ""})
        return buf.getvalue()

    if fmt == ExportFormat.MARKDOWN:
        lines = ["| Version | Change Type | Column | Detail |",
                 "|---------|-------------|--------|--------|"
                 ]
        for e in entries:
            lines.append(f"| {e.version} | {e.change_type} | {e.column} | {e.detail or ''} |")
        return "\n".join(lines)

    raise ValueError(f"Unsupported format: {fmt}")
