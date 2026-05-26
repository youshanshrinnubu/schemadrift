"""Assigns blame metadata to drift changes based on version and source context."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType


@dataclass
class BlameEntry:
    source: str
    version: str
    column: str
    change_type: str
    note: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "version": self.version,
            "column": self.column,
            "change_type": self.change_type,
            "note": self.note,
            "tags": self.tags,
        }


@dataclass
class BlameSummary:
    source: str
    version: str
    entries: List[BlameEntry] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "version": self.version,
            "entries": [e.to_dict() for e in self.entries],
        }

    @property
    def has_blame(self) -> bool:
        return len(self.entries) > 0


def _change_type_label(ct: ChangeType) -> str:
    return ct.value if hasattr(ct, "value") else str(ct)


def build_blame(
    report: DriftReport,
    notes: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, List[str]]] = None,
) -> BlameSummary:
    """Build a BlameSummary from a DriftReport, optionally attaching notes and tags per column."""
    notes = notes or {}
    tags = tags or {}
    entries = []
    for change in report.changes:
        entry = BlameEntry(
            source=report.source,
            version=report.new_version,
            column=change.column,
            change_type=_change_type_label(change.change_type),
            note=notes.get(change.column),
            tags=tags.get(change.column, []),
        )
        entries.append(entry)
    return BlameSummary(source=report.source, version=report.new_version, entries=entries)


def build_blame_for_reports(
    reports: List[DriftReport],
    notes: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, List[str]]] = None,
) -> List[BlameSummary]:
    """Build blame summaries for a list of drift reports."""
    return [build_blame(r, notes=notes, tags=tags) for r in reports]
