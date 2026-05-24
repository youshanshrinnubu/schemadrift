"""Tests for schemadrift.schema_search."""

import pytest
from datetime import datetime

from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_search import (
    SearchQuery,
    search_snapshots,
    find_columns_by_type,
    find_nullable_columns,
)


def make_snapshot(
    source: str = "db.users",
    version: str = "v1",
    columns=None,
) -> SchemaSnapshot:
    if columns is None:
        columns = [
            ColumnSchema(name="id", data_type="integer", nullable=False),
            ColumnSchema(name="email", data_type="varchar", nullable=False),
            ColumnSchema(name="bio", data_type="text", nullable=True),
        ]
    return SchemaSnapshot(
        source=source,
        version=version,
        captured_at=datetime(2024, 1, 1),
        columns=columns,
    )


def test_empty_snapshots_returns_empty():
    results = search_snapshots([], SearchQuery(column_name="id"))
    assert results == []


def test_column_name_substring_match():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(column_name="mai"))
    assert len(results) == 1
    assert results[0].column_name == "email"


def test_column_name_case_insensitive():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(column_name="EMAIL"))
    assert len(results) == 1
    assert results[0].column_name == "email"


def test_column_type_exact_match():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(column_type="varchar"))
    assert len(results) == 1
    assert results[0].column_name == "email"


def test_nullable_filter_true():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(nullable=True))
    assert len(results) == 1
    assert results[0].column_name == "bio"


def test_nullable_filter_false():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(nullable=False))
    assert len(results) == 2
    names = {r.column_name for r in results}
    assert names == {"id", "email"}


def test_source_filter_excludes_other_sources():
    snap1 = make_snapshot(source="db.users", version="v1")
    snap2 = make_snapshot(source="db.orders", version="v1")
    results = search_snapshots([snap1, snap2], SearchQuery(source="db.orders"))
    assert all(r.source == "db.orders" for r in results)
    assert len(results) == 3


def test_version_filter():
    snap1 = make_snapshot(version="v1")
    snap2 = make_snapshot(version="v2")
    results = search_snapshots([snap1, snap2], SearchQuery(version="v2"))
    assert all(r.version == "v2" for r in results)


def test_combined_filters():
    snap = make_snapshot()
    results = search_snapshots(
        [snap], SearchQuery(column_type="integer", nullable=False)
    )
    assert len(results) == 1
    assert results[0].column_name == "id"


def test_find_columns_by_type_convenience():
    snap = make_snapshot()
    results = find_columns_by_type([snap], "text")
    assert len(results) == 1
    assert results[0].column_name == "bio"


def test_find_nullable_columns_convenience():
    snap = make_snapshot()
    results = find_nullable_columns([snap], nullable=False)
    assert len(results) == 2


def test_result_to_dict_has_expected_keys():
    snap = make_snapshot()
    results = search_snapshots([snap], SearchQuery(column_name="id"))
    assert len(results) == 1
    d = results[0].to_dict()
    assert set(d.keys()) == {"source", "version", "column_name", "column_type", "nullable"}
