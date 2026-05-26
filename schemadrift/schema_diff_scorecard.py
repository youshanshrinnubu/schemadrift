from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class ScorecardEntry:
    source: str
    total_versions: int
    versions_with_drift: int
    total_changes: int
    added: int
    removed: int
    type_changed: int
    drift_rate: float  # versions_with_drift / total_versions
    health_score: float  # 0.0 (bad) to 1.0 (perfect)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_versions": self.total_versions,
            "versions_with_drift": self.versions_with_drift,
            "total_changes": self.total_changes,
            "added": self.added,
            "removed": self.removed,
            "type_changed": self.type_changed,
            "drift_rate": round(self.drift_rate, 4),
            "health_score": round(self.health_score, 4),
        }


@dataclass
class DriftScorecard:
    entries: List[ScorecardEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    def top_healthy(self, n: int = 5) -> List[ScorecardEntry]:
        return sorted(self.entries, key=lambda e: e.health_score, reverse=True)[:n]

    def top_drifting(self, n: int = 5) -> List[ScorecardEntry]:
        return sorted(self.entries, key=lambda e: e.drift_rate, reverse=True)[:n]


def _compute_health(drift_rate: float, removed: int, total_changes: int) -> float:
    """Health score penalises high drift rate and removals more heavily."""
    if total_changes == 0 and drift_rate == 0.0:
        return 1.0
    removal_penalty = min(removed * 0.05, 0.4)
    score = max(0.0, 1.0 - drift_rate - removal_penalty)
    return round(score, 4)


def build_scorecard(reports_by_source: Dict[str, List[DriftReport]]) -> DriftScorecard:
    entries: List[ScorecardEntry] = []
    for source, reports in reports_by_source.items():
        total_versions = len(reports)
        versions_with_drift = sum(1 for r in reports if r.has_drift())
        added = sum(
            1 for r in reports for c in r.changes if c.change_type == ChangeType.ADDED
        )
        removed = sum(
            1 for r in reports for c in r.changes if c.change_type == ChangeType.REMOVED
        )
        type_changed = sum(
            1 for r in reports for c in r.changes if c.change_type == ChangeType.TYPE_CHANGED
        )
        total_changes = added + removed + type_changed
        drift_rate = versions_with_drift / total_versions if total_versions > 0 else 0.0
        health = _compute_health(drift_rate, removed, total_changes)
        entries.append(
            ScorecardEntry(
                source=source,
                total_versions=total_versions,
                versions_with_drift=versions_with_drift,
                total_changes=total_changes,
                added=added,
                removed=removed,
                type_changed=type_changed,
                drift_rate=drift_rate,
                health_score=health,
            )
        )
    return DriftScorecard(entries=entries)
