"""Tests for history_analyzer module."""

import pytest
from unittest.mock import MagicMock
from schemadrift.history_analyzer import (
    compare_consecutive,
    analyze_source_history,
    find_first_drift_version,
    columns_ever_removed,
)
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.drift_detector import ChangeType
from datetime import datetime


def make_snapshot(source, version, columns):
    cols = [ColumnSchema(name=c["name"], data_type=c["type"], nullable=c.get("nullable", True)) for c in columns]
    return SchemaSnapshot(source=source, version=version, captured_at=datetime.utcnow(), columns=cols)


def test_compare_consecutive_no_changes():
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}])
    s2 = make_snapshot("src", "v2", [{"name": "id", "type": "int"}])
    reports = compare_consecutive([s1, s2])
    assert len(reports) == 1
    assert not reports[0].has_drift()


def test_compare_consecutive_detects_addition():
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}])
    s2 = make_snapshot("src", "v2", [{"name": "id", "type": "int"}, {"name": "name", "type": "str"}])
    reports = compare_consecutive([s1, s2])
    assert reports[0].has_drift()


def test_compare_consecutive_single_snapshot_returns_empty():
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}])
    reports = compare_consecutive([s1])
    assert reports == []


def test_analyze_source_history_returns_summary():
    store = MagicMock()
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}])
    s2 = make_snapshot("src", "v2", [{"name": "id", "type": "int"}, {"name": "email", "type": "str"}])
    store.load_all.return_value = [s1, s2]
    reports, summary = analyze_source_history(store, "src")
    assert summary.total_versions_compared == 1
    assert summary.added_columns == 1


def test_analyze_source_history_limit():
    store = MagicMock()
    snaps = [make_snapshot("src", f"v{i}", [{"name": "id", "type": "int"}]) for i in range(5)]
    store.load_all.return_value = snaps
    reports, summary = analyze_source_history(store, "src", limit=2)
    assert summary.total_versions_compared == 1


def test_find_first_drift_version_none_when_no_drift():
    store = MagicMock()
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}])
    s2 = make_snapshot("src", "v2", [{"name": "id", "type": "int"}])
    store.load_all.return_value = [s1, s2]
    reports, _ = analyze_source_history(store, "src")
    assert find_first_drift_version(reports) is None


def test_columns_ever_removed():
    store = MagicMock()
    s1 = make_snapshot("src", "v1", [{"name": "id", "type": "int"}, {"name": "old_col", "type": "str"}])
    s2 = make_snapshot("src", "v2", [{"name": "id", "type": "int"}])
    store.load_all.return_value = [s1, s2]
    reports, _ = analyze_source_history(store, "src")
    removed = columns_ever_removed(reports)
    assert "old_col" in removed
