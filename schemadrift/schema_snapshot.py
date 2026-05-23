"""Schema snapshot module for capturing and representing data source schemas."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ColumnSchema:
    """Represents a single column's schema metadata."""
    name: str
    dtype: str
    nullable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "nullable": self.nullable,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ColumnSchema":
        return cls(
            name=data["name"],
            dtype=data["dtype"],
            nullable=data.get("nullable", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SchemaSnapshot:
    """Captures the schema of a data source at a specific point in time."""
    source_id: str
    version: str
    captured_at: datetime
    columns: list[ColumnSchema] = field(default_factory=list)

    @classmethod
    def capture(cls, source_id: str, version: str, columns: list[ColumnSchema]) -> "SchemaSnapshot":
        """Create a new snapshot with the current UTC timestamp."""
        return cls(
            source_id=source_id,
            version=version,
            captured_at=datetime.now(timezone.utc),
            columns=columns,
        )

    def column_map(self) -> dict[str, ColumnSchema]:
        """Return columns indexed by name for fast lookup."""
        return {col.name: col for col in self.columns}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "version": self.version,
            "captured_at": self.captured_at.isoformat(),
            "columns": [col.to_dict() for col in self.columns],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaSnapshot":
        return cls(
            source_id=data["source_id"],
            version=data["version"],
            captured_at=datetime.fromisoformat(data["captured_at"]),
            columns=[ColumnSchema.from_dict(c) for c in data.get("columns", [])],
        )
