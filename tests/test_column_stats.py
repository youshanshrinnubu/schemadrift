"""Tests for schemadrift.column_stats module."""

import pytest
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.column_stats import compute_column_stats, ColumnStatsReport


def make_snapshot(version: str, columns: list) -> SchemaSnapshot:
    return SchemaSnapshot(
        source="test_source",
        version=version,
        columns=[ColumnSchema(name=c[0], data_type=c[1]) for c in columns],
    )


def test_returns_none_for_empty_list():
    result = compute_column_stats([])
    assert result is None


def test_single_snapshot_all_columns_in_one_version():
    snap = make_snapshot("v1", [("id", "int"), ("name", "str")])
    report = compute_column_stats([snap])
    assert report is not None
    assert report.total_versions_analyzed == 1
    assert "id" in report.stats
    assert "name" in report.stats
    assert report.stats["id"].appears_in_versions == ["v1"]


def test_columns_present_in_all_versions():
    snap1 = make_snapshot("v1", [("id", "int"), ("name", "str")])
    snap2 = make_snapshot("v2", [("id", "int"), ("name", "str"), ("email", "str")])
    report = compute_column_stats([snap1, snap2])
    stable = report.columns_present_in_all_versions()
    assert "id" in stable
    assert "name" in stable
    assert "email" not in stable


def test_type_change_increments_counter():
    snap1 = make_snapshot("v1", [("score", "int")])
    snap2 = make_snapshot("v2", [("score", "float")])
    snap3 = make_snapshot("v3", [("score", "str")])
    report = compute_column_stats([snap1, snap2, snap3])
    assert report.stats["score"].type_changes == 2


def test_no_type_change_when_type_stable():
    snap1 = make_snapshot("v1", [("id", "int")])
    snap2 = make_snapshot("v2", [("id", "int")])
    report = compute_column_stats([snap1, snap2])
    assert report.stats["id"].type_changes == 0


def test_most_changed_columns_sorted():
    snap1 = make_snapshot("v1", [("a", "int"), ("b", "int")])
    snap2 = make_snapshot("v2", [("a", "str"), ("b", "int")])
    snap3 = make_snapshot("v3", [("a", "float"), ("b", "int")])
    report = compute_column_stats([snap1, snap2, snap3])
    top = report.most_changed_columns(top_n=2)
    assert top[0].column_name == "a"
    assert top[0].type_changes == 2
    assert top[1].column_name == "b"
    assert top[1].type_changes == 0


def test_to_dict_structure():
    snap = make_snapshot("v1", [("id", "int")])
    report = compute_column_stats([snap])
    d = report.to_dict()
    assert d["source"] == "test_source"
    assert d["total_versions_analyzed"] == 1
    assert "id" in d["stats"]
    assert d["stats"]["id"]["data_type"] == "int"
    assert d["stats"]["id"]["type_changes"] == 0
