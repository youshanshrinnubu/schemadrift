"""Generates a periodic digest summarizing drift activity across sources."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from schemadrift.drift_detector import DriftReport, ChangeType
from schemadrift.schema_diff_stats import DriftStatsReport, compute_stats


@dataclass
class DigestEntry:
    source: str
    total_versions_checked: int
    total_changes: int
    added: int
    removed: int
    type_changed: int
    nullable_changed: int
    first_seen: Optional[str]
    last_seen: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "total_versions_checked": self.total_versions_checked,
            "total_changes": self.total_changes,
            "added": self.added,
            "removed": self.removed,
            "type_changed": self.type_changed,
            "nullable_changed": self.nullable_changed,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class DriftDigest:
    generated_at: str
    total_sources: int
    sources_with_drift: int
    entries: List[DigestEntry] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "generated_at": self.generated_at,
            "total_sources": self.total_sources,
            "sources_with_drift": self.sources_with_drift,
            "entries": [e.to_dict() for e in self.entries],
        }


def build_digest(reports_by_source: Dict[str, List[DriftReport]]) -> DriftDigest:
    """Build a digest from a mapping of source name to list of DriftReports."""
    entries: List[DigestEntry] = []
    sources_with_drift = 0

    for source, reports in sorted(reports_by_source.items()):
        added = removed = type_changed = nullable_changed = 0
        versions = set()
        timestamps = []

        for report in reports:
            versions.add(report.to_version)
            versions.add(report.from_version)
            if report.timestamp:
                timestamps.append(report.timestamp)
            for change in report.changes:
                if change.change_type == ChangeType.COLUMN_ADDED:
                    added += 1
                elif change.change_type == ChangeType.COLUMN_REMOVED:
                    removed += 1
                elif change.change_type == ChangeType.TYPE_CHANGED:
                    type_changed += 1
                elif change.change_type == ChangeType.NULLABLE_CHANGED:
                    nullable_changed += 1

        total_changes = added + removed + type_changed + nullable_changed
        if total_changes > 0:
            sources_with_drift += 1

        timestamps_sorted = sorted(timestamps)
        entries.append(DigestEntry(
            source=source,
            total_versions_checked=len(versions),
            total_changes=total_changes,
            added=added,
            removed=removed,
            type_changed=type_changed,
            nullable_changed=nullable_changed,
            first_seen=timestamps_sorted[0] if timestamps_sorted else None,
            last_seen=timestamps_sorted[-1] if timestamps_sorted else None,
        ))

    return DriftDigest(
        generated_at=datetime.utcnow().isoformat(),
        total_sources=len(reports_by_source),
        sources_with_drift=sources_with_drift,
        entries=entries,
    )
