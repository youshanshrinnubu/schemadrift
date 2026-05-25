"""Rollup aggregation of drift reports across sources and time windows."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class SourceRollup:
    source: str
    total_reports: int
    reports_with_drift: int
    change_type_counts: Dict[str, int] = field(default_factory=dict)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_reports": self.total_reports,
            "reports_with_drift": self.reports_with_drift,
            "change_type_counts": self.change_type_counts,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class DriftRollup:
    window_start: Optional[str]
    window_end: Optional[str]
    sources: Dict[str, SourceRollup] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "window_start": self.window_start,
            "window_end": self.window_end,
            "sources": {k: v.to_dict() for k, v in self.sources.items()},
        }

    @property
    def total_sources_with_drift(self) -> int:
        return sum(1 for s in self.sources.values() if s.reports_with_drift > 0)


def rollup_reports(
    reports: List[DriftReport],
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
) -> DriftRollup:
    """Aggregate a list of DriftReports into a per-source rollup."""
    rollup = DriftRollup(window_start=window_start, window_end=window_end)

    for report in reports:
        source = report.source
        if source not in rollup.sources:
            rollup.sources[source] = SourceRollup(
                source=source,
                total_reports=0,
                reports_with_drift=0,
            )

        entry = rollup.sources[source]
        entry.total_reports += 1

        ts = report.generated_at
        if ts:
            if entry.first_seen is None or ts < entry.first_seen:
                entry.first_seen = ts
            if entry.last_seen is None or ts > entry.last_seen:
                entry.last_seen = ts

        if report.has_drift():
            entry.reports_with_drift += 1
            for change in report.changes:
                key = change.change_type.value
                entry.change_type_counts[key] = entry.change_type_counts.get(key, 0) + 1

    return rollup
