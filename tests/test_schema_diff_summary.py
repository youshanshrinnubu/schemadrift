"""Tests for schema_diff_summary module."""

import pytest
from schemadrift.schema_diff_summary import summarize_reports, DriftSummary
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType


def make_report(changes):
    return DriftReport(
        source="test_source",
        from_version="v1",
        to_version="v2",
        changes=changes,
    )


def make_change(col, change_type, before=None, after=None):
    return DriftChange(
        column_name=col,
        change_type=change_type,
        before=before,
        after=after,
    )


def test_empty_reports_returns_zero_summary():
    summary = summarize_reports("src", [])
    assert summary.total_changes == 0
    assert summary.has_any_drift is False
    assert summary.total_versions_compared == 0


def test_single_report_added_column():
    report = make_report([make_change("col_a", ChangeType.COLUMN_ADDED)])
    summary = summarize_reports("src", [report])
    assert summary.added_columns == 1
    assert summary.removed_columns == 0
    assert summary.total_changes == 1
    assert summary.has_any_drift is True


def test_multiple_reports_aggregated():
    r1 = make_report([
        make_change("col_a", ChangeType.COLUMN_ADDED),
        make_change("col_b", ChangeType.COLUMN_REMOVED),
    ])
    r2 = make_report([
        make_change("col_c", ChangeType.TYPE_CHANGED, before="int", after="str"),
        make_change("col_d", ChangeType.NULLABLE_CHANGED, before="false", after="true"),
    ])
    summary = summarize_reports("src", [r1, r2])
    assert summary.total_versions_compared == 2
    assert summary.added_columns == 1
    assert summary.removed_columns == 1
    assert summary.type_changes == 1
    assert summary.nullable_changes == 1
    assert summary.total_changes == 4


def test_most_changed_columns_ordered():
    changes = [
        make_change("col_x", ChangeType.COLUMN_ADDED),
        make_change("col_x", ChangeType.COLUMN_REMOVED),
        make_change("col_y", ChangeType.TYPE_CHANGED),
    ]
    report = make_report(changes)
    summary = summarize_reports("src", [report])
    assert summary.most_changed_columns[0] == "col_x"


def test_to_dict_keys():
    summary = summarize_reports("src", [])
    d = summary.to_dict()
    assert "source" in d
    assert "total_changes" in d
    assert "most_changed_columns" in d
    assert "has_any_drift" in d


def test_source_preserved():
    summary = summarize_reports("my_db.orders", [])
    assert summary.source == "my_db.orders"
