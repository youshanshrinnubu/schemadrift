"""Tests for schema_diff_timeline module."""

import pytest
from unittest.mock import MagicMock

from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_diff_timeline import build_timeline, DriftTimeline, TimelineEntry


def make_snapshot(version: str, columns: list) -> SchemaSnapshot:
    cols = [ColumnSchema(name=c[0], data_type=c[1]) for c in columns]
    return SchemaSnapshot(
        source="orders",
        version=version,
        captured_at=f"2024-01-{version.zfill(2)}T00:00:00",
        columns=cols,
    )


def make_store(snapshots: list) -> MagicMock:
    store = MagicMock()
    store.load_all.return_value = snapshots
    return store


def test_empty_source_returns_empty_timeline():
    store = make_store([])
    timeline = build_timeline("orders", store)
    assert isinstance(timeline, DriftTimeline)
    assert timeline.entries == []


def test_single_snapshot_returns_empty_timeline():
    store = make_store([make_snapshot("1", [("id", "int")])])
    timeline = build_timeline("orders", store)
    assert timeline.entries == []


def test_no_changes_between_identical_snapshots():
    s1 = make_snapshot("1", [("id", "int"), ("name", "str")])
    s2 = make_snapshot("2", [("id", "int"), ("name", "str")])
    store = make_store([s1, s2])
    timeline = build_timeline("orders", store)
    assert len(timeline.entries) == 1
    assert timeline.entries[0].total_changes == 0
    assert timeline.entries[0].version == "2"


def test_detects_added_column():
    s1 = make_snapshot("1", [("id", "int")])
    s2 = make_snapshot("2", [("id", "int"), ("email", "str")])
    store = make_store([s1, s2])
    timeline = build_timeline("orders", store)
    entry = timeline.entries[0]
    assert "email" in entry.added
    assert entry.total_changes == 1


def test_detects_removed_column():
    s1 = make_snapshot("1", [("id", "int"), ("legacy", "str")])
    s2 = make_snapshot("2", [("id", "int")])
    store = make_store([s1, s2])
    timeline = build_timeline("orders", store)
    entry = timeline.entries[0]
    assert "legacy" in entry.removed
    assert entry.total_changes == 1


def test_versions_with_drift_filters_correctly():
    s1 = make_snapshot("1", [("id", "int")])
    s2 = make_snapshot("2", [("id", "int")])
    s3 = make_snapshot("3", [("id", "int"), ("new_col", "str")])
    store = make_store([s1, s2, s3])
    timeline = build_timeline("orders", store)
    assert "3" in timeline.versions_with_drift()
    assert "2" not in timeline.versions_with_drift()


def test_peak_change_version():
    s1 = make_snapshot("1", [("id", "int")])
    s2 = make_snapshot("2", [("id", "int"), ("a", "str")])
    s3 = make_snapshot("3", [("id", "int"), ("a", "str"), ("b", "float"), ("c", "bool")])
    store = make_store([s1, s2, s3])
    timeline = build_timeline("orders", store)
    assert timeline.peak_change_version() == "3"


def test_to_dict_structure():
    s1 = make_snapshot("1", [("id", "int")])
    s2 = make_snapshot("2", [("id", "int"), ("name", "str")])
    store = make_store([s1, s2])
    timeline = build_timeline("orders", store)
    d = timeline.to_dict()
    assert d["source"] == "orders"
    assert isinstance(d["entries"], list)
    assert "added" in d["entries"][0]
    assert "removed" in d["entries"][0]
    assert "total_changes" in d["entries"][0]
