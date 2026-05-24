"""Builds a timeline of schema changes across versions for a given source."""

from dataclasses import dataclass, field
from typing import List, Optional

from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import DriftReport, compare_schemas
from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class TimelineEntry:
    version: str
    timestamp: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    type_changed: List[str] = field(default_factory=list)
    total_changes: int = 0

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "added": self.added,
            "removed": self.removed,
            "type_changed": self.type_changed,
            "total_changes": self.total_changes,
        }


@dataclass
class DriftTimeline:
    source: str
    entries: List[TimelineEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "entries": [e.to_dict() for e in self.entries],
        }

    def versions_with_drift(self) -> List[str]:
        return [e.version for e in self.entries if e.total_changes > 0]

    def peak_change_version(self) -> Optional[str]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.total_changes).version


def build_timeline(source: str, store: SnapshotStore) -> DriftTimeline:
    """Build a drift timeline for a source by comparing consecutive snapshots."""
    snapshots: List[SchemaSnapshot] = store.load_all(source)
    timeline = DriftTimeline(source=source)

    if len(snapshots) < 2:
        return timeline

    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        report: DriftReport = compare_schemas(prev, curr)

        added = [c.column_name for c in report.changes if c.change_type.value == "added"]
        removed = [c.column_name for c in report.changes if c.change_type.value == "removed"]
        type_changed = [c.column_name for c in report.changes if c.change_type.value == "type_changed"]

        entry = TimelineEntry(
            version=curr.version,
            timestamp=curr.captured_at,
            added=added,
            removed=removed,
            type_changed=type_changed,
            total_changes=len(report.changes),
        )
        timeline.entries.append(entry)

    return timeline
