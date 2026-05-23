"""Drift detection logic for comparing two schema snapshots."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from schemadrift.schema_snapshot import SchemaSnapshot


class ChangeType(str, Enum):
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    TYPE_CHANGED = "type_changed"
    NULLABILITY_CHANGED = "nullability_changed"


@dataclass
class DriftChange:
    """Represents a single detected schema change."""
    change_type: ChangeType
    column_name: str
    before: Any = None
    after: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "column_name": self.column_name,
            "before": self.before,
            "after": self.after,
        }


@dataclass
class DriftReport:
    """Summary of schema drift between two snapshots."""
    source_id: str
    from_version: str
    to_version: str
    changes: list[DriftChange] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.changes) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "has_drift": self.has_drift,
            "change_count": len(self.changes),
            "changes": [c.to_dict() for c in self.changes],
        }


def detect_drift(old: SchemaSnapshot, new: SchemaSnapshot) -> DriftReport:
    """Compare two snapshots and return a DriftReport describing all changes."""
    if old.source_id != new.source_id:
        raise ValueError(f"source_id mismatch: '{old.source_id}' vs '{new.source_id}'")

    report = DriftReport(source_id=old.source_id, from_version=old.version, to_version=new.version)
    old_cols = old.column_map()
    new_cols = new.column_map()

    for name, col in old_cols.items():
        if name not in new_cols:
            report.changes.append(DriftChange(ChangeType.COLUMN_REMOVED, name, before=col.dtype))
            continue
        new_col = new_cols[name]
        if col.dtype != new_col.dtype:
            report.changes.append(DriftChange(ChangeType.TYPE_CHANGED, name, before=col.dtype, after=new_col.dtype))
        if col.nullable != new_col.nullable:
            report.changes.append(DriftChange(ChangeType.NULLABILITY_CHANGED, name, before=col.nullable, after=new_col.nullable))

    for name, col in new_cols.items():
        if name not in old_cols:
            report.changes.append(DriftChange(ChangeType.COLUMN_ADDED, name, after=col.dtype))

    return report
