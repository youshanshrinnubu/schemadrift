"""Generates human-readable and structured summaries of schema drift over time."""

from dataclasses import dataclass, field
from typing import List, Optional
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class DriftSummary:
    source: str
    total_versions_compared: int
    total_changes: int
    added_columns: int
    removed_columns: int
    type_changes: int
    nullable_changes: int
    most_changed_columns: List[str] = field(default_factory=list)
    has_any_drift: bool = False

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_versions_compared": self.total_versions_compared,
            "total_changes": self.total_changes,
            "added_columns": self.added_columns,
            "removed_columns": self.removed_columns,
            "type_changes": self.type_changes,
            "nullable_changes": self.nullable_changes,
            "most_changed_columns": self.most_changed_columns,
            "has_any_drift": self.has_any_drift,
        }


def summarize_reports(source: str, reports: List[DriftReport]) -> DriftSummary:
    """Aggregate multiple DriftReports into a single DriftSummary."""
    added = removed = type_ch = nullable_ch = 0
    column_change_count: dict = {}

    for report in reports:
        for change in report.changes:
            col = change.column_name
            column_change_count[col] = column_change_count.get(col, 0) + 1
            if change.change_type == ChangeType.COLUMN_ADDED:
                added += 1
            elif change.change_type == ChangeType.COLUMN_REMOVED:
                removed += 1
            elif change.change_type == ChangeType.TYPE_CHANGED:
                type_ch += 1
            elif change.change_type == ChangeType.NULLABLE_CHANGED:
                nullable_ch += 1

    total = added + removed + type_ch + nullable_ch
    top_columns = sorted(column_change_count, key=lambda c: column_change_count[c], reverse=True)[:5]

    return DriftSummary(
        source=source,
        total_versions_compared=len(reports),
        total_changes=total,
        added_columns=added,
        removed_columns=removed,
        type_changes=type_ch,
        nullable_changes=nullable_ch,
        most_changed_columns=top_columns,
        has_any_drift=total > 0,
    )
