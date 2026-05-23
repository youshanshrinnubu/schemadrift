"""Tracks column rename and lineage hints across schema versions."""

from dataclasses import dataclass, field
from typing import Optional
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class LineageHint:
    """Represents a suspected column rename between two versions."""

    source: str
    old_name: str
    new_name: str
    version_from: str
    version_to: str
    confidence: float  # 0.0 - 1.0 based on type match and proximity

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "old_name": self.old_name,
            "new_name": self.new_name,
            "version_from": self.version_from,
            "version_to": self.version_to,
            "confidence": self.confidence,
        }


def _score_rename_candidate(removed_col, added_col, removed_type: str, added_type: str) -> float:
    """Score likelihood that removed and added column are a rename."""
    score = 0.0
    if removed_type == added_type:
        score += 0.6
    # Partial name similarity (shared prefix or suffix)
    shorter = min(len(removed_col), len(added_col))
    if shorter > 0:
        prefix_len = sum(1 for a, b in zip(removed_col, added_col) if a == b)
        score += 0.4 * (prefix_len / max(len(removed_col), len(added_col)))
    return round(min(score, 1.0), 3)


def detect_lineage_hints(
    report: DriftReport,
    min_confidence: float = 0.5,
) -> list[LineageHint]:
    """Analyse a DriftReport and return likely column rename hints."""
    removed = {
        c.column_name: c
        for c in report.changes
        if c.change_type == ChangeType.COLUMN_REMOVED
    }
    added = {
        c.column_name: c
        for c in report.changes
        if c.change_type == ChangeType.COLUMN_ADDED
    }

    hints: list[LineageHint] = []
    for rem_name, rem_change in removed.items():
        for add_name, add_change in added.items():
            score = _score_rename_candidate(
                rem_name,
                add_name,
                rem_change.before or "",
                add_change.after or "",
            )
            if score >= min_confidence:
                hints.append(
                    LineageHint(
                        source=report.source,
                        old_name=rem_name,
                        new_name=add_name,
                        version_from=report.version_from,
                        version_to=report.version_to,
                        confidence=score,
                    )
                )
    hints.sort(key=lambda h: h.confidence, reverse=True)
    return hints
