from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class SourceDriftStats:
    source: str
    total_versions_compared: int
    total_changes: int
    changes_by_type: Dict[str, int] = field(default_factory=dict)
    most_changed_version: str = ""
    most_changed_version_count: int = 0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_versions_compared": self.total_versions_compared,
            "total_changes": self.total_changes,
            "changes_by_type": self.changes_by_type,
            "most_changed_version": self.most_changed_version,
            "most_changed_version_count": self.most_changed_version_count,
        }


@dataclass
class DriftStatsReport:
    sources: List[SourceDriftStats] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"sources": [s.to_dict() for s in self.sources]}

    def total_changes(self) -> int:
        return sum(s.total_changes for s in self.sources)

    def most_active_source(self) -> str | None:
        if not self.sources:
            return None
        return max(self.sources, key=lambda s: s.total_changes).source


def compute_drift_stats(reports: List[DriftReport]) -> DriftStatsReport:
    """Aggregate drift statistics from a list of DriftReports grouped by source."""
    by_source: Dict[str, List[DriftReport]] = {}
    for report in reports:
        by_source.setdefault(report.source, []).append(report)

    stats_list: List[SourceDriftStats] = []
    for source, source_reports in by_source.items():
        total_changes = 0
        changes_by_type: Dict[str, int] = {}
        most_changed_version = ""
        most_changed_count = 0

        for report in source_reports:
            count = len(report.changes)
            total_changes += count
            for change in report.changes:
                key = change.change_type.value
                changes_by_type[key] = changes_by_type.get(key, 0) + 1
            if count > most_changed_count:
                most_changed_count = count
                most_changed_version = report.to_version

        stats_list.append(
            SourceDriftStats(
                source=source,
                total_versions_compared=len(source_reports),
                total_changes=total_changes,
                changes_by_type=changes_by_type,
                most_changed_version=most_changed_version,
                most_changed_version_count=most_changed_count,
            )
        )

    return DriftStatsReport(sources=stats_list)
