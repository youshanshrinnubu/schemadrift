"""Search and filter schema snapshots by column names, types, or tags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class SearchQuery:
    """Criteria used to filter snapshots or columns."""

    column_name: Optional[str] = None          # substring match
    column_type: Optional[str] = None          # exact match
    source: Optional[str] = None               # exact match
    version: Optional[str] = None              # exact match
    nullable: Optional[bool] = None            # exact match


@dataclass
class SearchResult:
    """A single matching column within a snapshot."""

    source: str
    version: str
    column_name: str
    column_type: str
    nullable: bool

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "column_name": self.column_name,
            "column_type": self.column_type,
            "nullable": self.nullable,
        }


def search_snapshots(
    snapshots: List[SchemaSnapshot],
    query: SearchQuery,
) -> List[SearchResult]:
    """Return all columns across *snapshots* that match every criterion in *query*."""
    results: List[SearchResult] = []

    for snap in snapshots:
        if query.source is not None and snap.source != query.source:
            continue
        if query.version is not None and snap.version != query.version:
            continue

        for col in snap.columns:
            if query.column_name is not None and query.column_name.lower() not in col.name.lower():
                continue
            if query.column_type is not None and col.data_type != query.column_type:
                continue
            if query.nullable is not None and col.nullable != query.nullable:
                continue

            results.append(
                SearchResult(
                    source=snap.source,
                    version=snap.version,
                    column_name=col.name,
                    column_type=col.data_type,
                    nullable=col.nullable,
                )
            )

    return results


def find_columns_by_type(
    snapshots: List[SchemaSnapshot],
    data_type: str,
) -> List[SearchResult]:
    """Convenience wrapper: find all columns with a specific data type."""
    return search_snapshots(snapshots, SearchQuery(column_type=data_type))


def find_nullable_columns(
    snapshots: List[SchemaSnapshot],
    nullable: bool = True,
) -> List[SearchResult]:
    """Convenience wrapper: find all (non-)nullable columns."""
    return search_snapshots(snapshots, SearchQuery(nullable=nullable))
