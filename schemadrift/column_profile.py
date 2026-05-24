"""Column profile tracking: captures nullable, unique, and default metadata per column."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    nullable: bool = True
    unique: bool = False
    default: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "nullable": self.nullable,
            "unique": self.unique,
            "default": self.default,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnProfile":
        return cls(
            name=data["name"],
            dtype=data["dtype"],
            nullable=data.get("nullable", True),
            unique=data.get("unique", False),
            default=data.get("default"),
        )


@dataclass
class SchemaProfile:
    source: str
    version: str
    columns: List[ColumnProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "version": self.version,
            "columns": [c.to_dict() for c in self.columns],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaProfile":
        return cls(
            source=data["source"],
            version=data["version"],
            columns=[ColumnProfile.from_dict(c) for c in data.get("columns", [])],
        )

    def column_map(self) -> Dict[str, ColumnProfile]:
        return {c.name: c for c in self.columns}


def diff_profiles(old: SchemaProfile, new: SchemaProfile) -> List[Dict[str, Any]]:
    """Return a list of profile-level changes between two SchemaProfiles."""
    changes: List[Dict[str, Any]] = []
    old_map = old.column_map()
    new_map = new.column_map()

    for name, new_col in new_map.items():
        if name not in old_map:
            continue
        old_col = old_map[name]
        for attr in ("nullable", "unique", "default"):
            old_val = getattr(old_col, attr)
            new_val = getattr(new_col, attr)
            if old_val != new_val:
                changes.append({
                    "column": name,
                    "attribute": attr,
                    "before": old_val,
                    "after": new_val,
                })
    return changes
