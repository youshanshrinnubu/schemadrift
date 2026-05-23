"""Tests for schema snapshot and drift detection."""

import pytest

from schemadrift.drift_detector import ChangeType, detect_drift
from schemadrift.schema_snapshot import ColumnSchema, SchemaSnapshot


def make_snapshot(source_id: str, version: str, columns: list[tuple]) -> SchemaSnapshot:
    cols = [ColumnSchema(name=n, dtype=d, nullable=nu) for n, d, nu in columns]
    return SchemaSnapshot.capture(source_id, version, cols)


BASE_COLS = [("id", "int", False), ("name", "varchar", True), ("score", "float", True)]


def test_no_drift_identical_schemas():
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", BASE_COLS)
    report = detect_drift(old, new)
    assert not report.has_drift
    assert report.changes == []


def test_column_added():
    new_cols = BASE_COLS + [("email", "varchar", True)]
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", new_cols)
    report = detect_drift(old, new)
    assert report.has_drift
    assert any(c.change_type == ChangeType.COLUMN_ADDED and c.column_name == "email" for c in report.changes)


def test_column_removed():
    reduced_cols = [("id", "int", False), ("name", "varchar", True)]
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", reduced_cols)
    report = detect_drift(old, new)
    assert report.has_drift
    assert any(c.change_type == ChangeType.COLUMN_REMOVED and c.column_name == "score" for c in report.changes)


def test_type_changed():
    changed_cols = [("id", "int", False), ("name", "text", True), ("score", "float", True)]
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", changed_cols)
    report = detect_drift(old, new)
    assert report.has_drift
    change = next(c for c in report.changes if c.column_name == "name")
    assert change.change_type == ChangeType.TYPE_CHANGED
    assert change.before == "varchar"
    assert change.after == "text"


def test_nullability_changed():
    changed_cols = [("id", "int", True), ("name", "varchar", True), ("score", "float", True)]
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", changed_cols)
    report = detect_drift(old, new)
    assert report.has_drift
    change = next(c for c in report.changes if c.column_name == "id")
    assert change.change_type == ChangeType.NULLABILITY_CHANGED


def test_source_id_mismatch_raises():
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds2", "v2", BASE_COLS)
    with pytest.raises(ValueError, match="source_id mismatch"):
        detect_drift(old, new)


def test_report_to_dict_structure():
    new_cols = BASE_COLS + [("created_at", "timestamp", True)]
    old = make_snapshot("ds1", "v1", BASE_COLS)
    new = make_snapshot("ds1", "v2", new_cols)
    report = detect_drift(old, new)
    d = report.to_dict()
    assert d["source_id"] == "ds1"
    assert d["has_drift"] is True
    assert d["change_count"] == 1
    assert isinstance(d["changes"], list)
