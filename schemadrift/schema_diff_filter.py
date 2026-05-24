"""Filter drift reports by change type, column name, or source."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schemadrift.drift_detector import ChangeType, DriftReport


@dataclass
class DriftFilter:
    """Criteria for filtering drift reports and their changes."""

    sources: List[str] = field(default_factory=list)
    change_types: List[ChangeType] = field(default_factory=list)
    column_name_contains: Optional[str] = None

    def is_empty(self) -> bool:
        return (
            not self.sources
            and not self.change_types
            and self.column_name_contains is None
        )


def _matches_filter(change, drift_filter: DriftFilter) -> bool:
    """Return True if a single DriftChange passes all filter criteria."""
    if drift_filter.change_types and change.change_type not in drift_filter.change_types:
        return False
    if drift_filter.column_name_contains:
        needle = drift_filter.column_name_contains.lower()
        if needle not in change.column_name.lower():
            return False
    return True


def filter_report(report: DriftReport, drift_filter: DriftFilter) -> DriftReport:
    """Return a new DriftReport containing only changes that match the filter."""
    if drift_filter.is_empty():
        return report

    filtered_changes = [
        c for c in report.changes if _matches_filter(c, drift_filter)
    ]

    return DriftReport(
        source=report.source,
        from_version=report.from_version,
        to_version=report.to_version,
        changes=filtered_changes,
    )


def filter_reports(
    reports: List[DriftReport], drift_filter: DriftFilter
) -> List[DriftReport]:
    """Filter a list of DriftReports, optionally restricting to specific sources."""
    result = []
    for report in reports:
        if drift_filter.sources and report.source not in drift_filter.sources:
            continue
        filtered = filter_report(report, drift_filter)
        result.append(filtered)
    return result
