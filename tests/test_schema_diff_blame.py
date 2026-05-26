"""Tests for schema_diff_blame module."""

import pytest
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.drift_detector import compare_snapshots, ChangeType
from schemadrift.schema_diff_blame import build_blame, build_blame_for_reports, BlameEntry, BlameSummary


def make_snapshot(source, version, columns):
    cols = [ColumnSchema(name=c[0], data_type=c[1]) for c in columns]
    return SchemaSnapshot(source=source, version=version, columns=cols)


def make_report(source="db.table", old_cols=None, new_cols=None, old_ver="v1", new_ver="v2"):
    old_cols = old_cols or [("id", "int")]
    new_cols = new_cols or [("id", "int")]
    s1 = make_snapshot(source, old_ver, old_cols)
    s2 = make_snapshot(source, new_ver, new_cols)
    return compare_snapshots(s1, s2)


def test_no_blame_when_no_drift():
    report = make_report(old_cols=[("id", "int")], new_cols=[("id", "int")])
    summary = build_blame(report)
    assert not summary.has_blame
    assert summary.entries == []


def test_blame_entry_for_added_column():
    report = make_report(
        old_cols=[("id", "int")],
        new_cols=[("id", "int"), ("email", "text")],
    )
    summary = build_blame(report)
    assert summary.has_blame
    assert len(summary.entries) == 1
    assert summary.entries[0].column == "email"
    assert summary.entries[0].change_type == "added"


def test_blame_entry_for_removed_column():
    report = make_report(
        old_cols=[("id", "int"), ("legacy", "text")],
        new_cols=[("id", "int")],
    )
    summary = build_blame(report)
    assert summary.has_blame
    assert summary.entries[0].column == "legacy"
    assert summary.entries[0].change_type == "removed"


def test_blame_attaches_notes():
    report = make_report(
        old_cols=[("id", "int")],
        new_cols=[("id", "int"), ("score", "float")],
    )
    notes = {"score": "Added for ML pipeline"}
    summary = build_blame(report, notes=notes)
    assert summary.entries[0].note == "Added for ML pipeline"


def test_blame_attaches_tags():
    report = make_report(
        old_cols=[("id", "int"), ("old_col", "text")],
        new_cols=[("id", "int")],
    )
    tags = {"old_col": ["deprecated", "breaking"]}
    summary = build_blame(report, tags=tags)
    assert "deprecated" in summary.entries[0].tags
    assert "breaking" in summary.entries[0].tags


def test_blame_to_dict_structure():
    report = make_report(
        old_cols=[("id", "int")],
        new_cols=[("id", "int"), ("name", "text")],
    )
    summary = build_blame(report)
    d = summary.to_dict()
    assert "source" in d
    assert "version" in d
    assert "entries" in d
    assert d["entries"][0]["column"] == "name"


def test_build_blame_for_multiple_reports():
    r1 = make_report(source="a", old_cols=[("id", "int")], new_cols=[("id", "int"), ("x", "text")])
    r2 = make_report(source="b", old_cols=[("id", "int"), ("y", "float")], new_cols=[("id", "int")])
    summaries = build_blame_for_reports([r1, r2])
    assert len(summaries) == 2
    assert summaries[0].source == "a"
    assert summaries[1].source == "b"
