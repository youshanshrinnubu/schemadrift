"""Tests for schema_changelog.py"""

import pytest
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_changelog import build_changelog, ChangelogEntry, Changelog


def make_snapshot(version: str, columns):
    cols = [ColumnSchema(name=n, data_type=t) for n, t in columns]
    return SchemaSnapshot(source="db.orders", version=version, columns=cols)


def make_report(old_snap, new_snap, changes):
    return DriftReport(old_snapshot=old_snap, new_snapshot=new_snap, changes=changes)


def test_no_drift_reports_returns_empty_changelog():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("id", "int")])
    report = make_report(snap_a, snap_b, [])
    changelog = build_changelog("db.orders", [report])
    assert changelog.source == "db.orders"
    assert changelog.entries == []


def test_added_column_appears_in_changelog():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("id", "int"), ("name", "str")])
    change = DriftChange(change_type=ChangeType.ADDED, column_name="name", new_type="str")
    report = make_report(snap_a, snap_b, [change])
    changelog = build_changelog("db.orders", [report])
    assert len(changelog.entries) == 1
    entry = changelog.entries[0]
    assert entry.version == "v2"
    assert "added" in entry.summary.lower()
    assert any("name" in d for d in entry.details)


def test_removed_column_appears_in_changelog():
    snap_a = make_snapshot("v1", [("id", "int"), ("old_col", "str")])
    snap_b = make_snapshot("v2", [("id", "int")])
    change = DriftChange(change_type=ChangeType.REMOVED, column_name="old_col", old_type="str")
    report = make_report(snap_a, snap_b, [change])
    changelog = build_changelog("db.orders", [report])
    assert len(changelog.entries) == 1
    assert "removed" in changelog.entries[0].summary.lower()


def test_type_change_reflected_in_detail():
    snap_a = make_snapshot("v1", [("amount", "int")])
    snap_b = make_snapshot("v2", [("amount", "float")])
    change = DriftChange(
        change_type=ChangeType.TYPE_CHANGED,
        column_name="amount",
        old_type="int",
        new_type="float",
    )
    report = make_report(snap_a, snap_b, [change])
    changelog = build_changelog("db.orders", [report])
    detail = changelog.entries[0].details[0]
    assert "int" in detail and "float" in detail


def test_multiple_reports_produce_multiple_entries():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("id", "int"), ("x", "str")])
    snap_c = make_snapshot("v3", [("id", "int"), ("x", "float")])
    change1 = DriftChange(change_type=ChangeType.ADDED, column_name="x", new_type="str")
    change2 = DriftChange(
        change_type=ChangeType.TYPE_CHANGED, column_name="x", old_type="str", new_type="float"
    )
    reports = [
        make_report(snap_a, snap_b, [change1]),
        make_report(snap_b, snap_c, [change2]),
    ]
    changelog = build_changelog("db.orders", reports)
    assert len(changelog.entries) == 2
    assert changelog.entries[0].version == "v2"
    assert changelog.entries[1].version == "v3"


def test_to_dict_structure():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("id", "int"), ("ts", "datetime")])
    change = DriftChange(change_type=ChangeType.ADDED, column_name="ts", new_type="datetime")
    report = make_report(snap_a, snap_b, [change])
    changelog = build_changelog("db.orders", [report])
    d = changelog.to_dict()
    assert d["source"] == "db.orders"
    assert isinstance(d["entries"], list)
    assert d["entries"][0]["version"] == "v2"
    assert "summary" in d["entries"][0]
    assert "details" in d["entries"][0]
