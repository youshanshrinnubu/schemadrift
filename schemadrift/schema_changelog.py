"""Generates a human-readable changelog from a sequence of drift reports."""

from dataclasses import dataclass, field
from typing import List, Optional
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class ChangelogEntry:
    version: str
    source: str
    summary: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "source": self.source,
            "summary": self.summary,
            "details": self.details,
        }


@dataclass
class Changelog:
    source: str
    entries: List[ChangelogEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "entries": [e.to_dict() for e in self.entries],
        }


def _summarize(report: DriftReport) -> str:
    if not report.changes:
        return "No schema changes."
    counts = {ct: 0 for ct in ChangeType}
    for change in report.changes:
        counts[change.change_type] += 1
    parts = []
    if counts[ChangeType.ADDED]:
        parts.append(f"{counts[ChangeType.ADDED]} column(s) added")
    if counts[ChangeType.REMOVED]:
        parts.append(f"{counts[ChangeType.REMOVED]} column(s) removed")
    if counts[ChangeType.TYPE_CHANGED]:
        parts.append(f"{counts[ChangeType.TYPE_CHANGED]} type change(s)")
    if counts[ChangeType.NULLABLE_CHANGED]:
        parts.append(f"{counts[ChangeType.NULLABLE_CHANGED]} nullability change(s)")
    return "; ".join(parts) if parts else "No schema changes."


def _detail_lines(report: DriftReport) -> List[str]:
    lines = []
    for change in report.changes:
        if change.change_type == ChangeType.ADDED:
            lines.append(f"+ Added column '{change.column_name}' ({change.new_type})")
        elif change.change_type == ChangeType.REMOVED:
            lines.append(f"- Removed column '{change.column_name}' ({change.old_type})")
        elif change.change_type == ChangeType.TYPE_CHANGED:
            lines.append(
                f"~ '{change.column_name}' type changed: {change.old_type} -> {change.new_type}"
            )
        elif change.change_type == ChangeType.NULLABLE_CHANGED:
            lines.append(f"~ '{change.column_name}' nullability changed")
    return lines


def build_changelog(source: str, reports: List[DriftReport]) -> Changelog:
    """Build a Changelog from an ordered list of DriftReports for a source."""
    entries = []
    for report in reports:
        if not report.changes:
            continue
        entry = ChangelogEntry(
            version=report.new_snapshot.version,
            source=source,
            summary=_summarize(report),
            details=_detail_lines(report),
        )
        entries.append(entry)
    return Changelog(source=source, entries=entries)
