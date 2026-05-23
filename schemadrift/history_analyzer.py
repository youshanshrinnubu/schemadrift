"""Analyzes full snapshot history to produce drift reports and summaries."""

from typing import List, Optional, Tuple
from schemadrift.snapshot_store import SnapshotStore
from schemadrift.schema_snapshot import SchemaSnapshot
from schemadrift.drift_detector import DriftReport, detect_drift
from schemadrift.schema_diff_summary import DriftSummary, summarize_reports


def compare_consecutive(
    snapshots: List[SchemaSnapshot],
) -> List[DriftReport]:
    """Compare each snapshot against the previous one in order."""
    reports = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        report = detect_drift(prev, curr)
        reports.append(report)
    return reports


def analyze_source_history(
    store: SnapshotStore,
    source: str,
    limit: Optional[int] = None,
) -> Tuple[List[DriftReport], DriftSummary]:
    """Load all snapshots for a source, compare consecutively, and summarize."""
    snapshots = store.load_all(source)
    if limit is not None:
        snapshots = snapshots[-limit:]

    if len(snapshots) < 2:
        reports: List[DriftReport] = []
    else:
        reports = compare_consecutive(snapshots)

    summary = summarize_reports(source, reports)
    return reports, summary


def find_first_drift_version(
    reports: List[DriftReport],
) -> Optional[str]:
    """Return the to_version of the first report that contains drift."""
    for report in reports:
        if report.has_drift():
            return report.to_version
    return None


def columns_ever_removed(
    reports: List[DriftReport],
) -> List[str]:
    """Return a sorted list of column names that were removed in any report."""
    from schemadrift.drift_detector import ChangeType
    removed = set()
    for report in reports:
        for change in report.changes:
            if change.change_type == ChangeType.COLUMN_REMOVED:
                removed.add(change.column_name)
    return sorted(removed)


def columns_ever_added(
    reports: List[DriftReport],
) -> List[str]:
    """Return a sorted list of column names that were added in any report.

    Useful for auditing schema growth over time or identifying columns that
    were introduced and potentially later removed.
    """
    from schemadrift.drift_detector import ChangeType
    added = set()
    for report in reports:
        for change in report.changes:
            if change.change_type == ChangeType.COLUMN_ADDED:
                added.add(change.column_name)
    return sorted(added)
