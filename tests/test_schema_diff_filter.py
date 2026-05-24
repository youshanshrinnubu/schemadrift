"""Tests for schema_diff_filter module."""

import pytest

from schemadrift.drift_detector import ChangeType, DriftChange, DriftReport
from schemadrift.schema_diff_filter import DriftFilter, filter_report, filter_reports


def make_change(column_name: str, change_type: ChangeType) -> DriftChange:
    return DriftChange(
        column_name=column_name,
        change_type=change_type,
        before="int" if change_type == ChangeType.TYPE_CHANGED else None,
        after="str" if change_type == ChangeType.TYPE_CHANGED else None,
    )


def make_report(source: str, *changes: DriftChange) -> DriftReport:
    return DriftReport(
        source=source,
        from_version="v1",
        to_version="v2",
        changes=list(changes),
    )


def test_empty_filter_returns_report_unchanged():
    report = make_report(
        "orders",
        make_change("id", ChangeType.COLUMN_ADDED),
        make_change("name", ChangeType.COLUMN_REMOVED),
    )
    result = filter_report(report, DriftFilter())
    assert len(result.changes) == 2


def test_filter_by_change_type_keeps_matching():
    report = make_report(
        "orders",
        make_change("id", ChangeType.COLUMN_ADDED),
        make_change("name", ChangeType.COLUMN_REMOVED),
    )
    f = DriftFilter(change_types=[ChangeType.COLUMN_ADDED])
    result = filter_report(report, f)
    assert len(result.changes) == 1
    assert result.changes[0].column_name == "id"


def test_filter_by_column_name_substring():
    report = make_report(
        "orders",
        make_change("user_id", ChangeType.COLUMN_ADDED),
        make_change("amount", ChangeType.COLUMN_ADDED),
    )
    f = DriftFilter(column_name_contains="user")
    result = filter_report(report, f)
    assert len(result.changes) == 1
    assert result.changes[0].column_name == "user_id"


def test_filter_column_name_is_case_insensitive():
    report = make_report("events", make_change("UserID", ChangeType.COLUMN_ADDED))
    f = DriftFilter(column_name_contains="userid")
    result = filter_report(report, f)
    assert len(result.changes) == 1


def test_filter_reports_by_source():
    r1 = make_report("orders", make_change("id", ChangeType.COLUMN_ADDED))
    r2 = make_report("users", make_change("email", ChangeType.COLUMN_REMOVED))
    f = DriftFilter(sources=["orders"])
    results = filter_reports([r1, r2], f)
    assert len(results) == 1
    assert results[0].source == "orders"


def test_filter_reports_no_source_filter_returns_all():
    r1 = make_report("orders", make_change("id", ChangeType.COLUMN_ADDED))
    r2 = make_report("users", make_change("email", ChangeType.COLUMN_REMOVED))
    results = filter_reports([r1, r2], DriftFilter())
    assert len(results) == 2


def test_combined_source_and_type_filter():
    r1 = make_report(
        "orders",
        make_change("id", ChangeType.COLUMN_ADDED),
        make_change("ts", ChangeType.TYPE_CHANGED),
    )
    r2 = make_report("users", make_change("name", ChangeType.COLUMN_ADDED))
    f = DriftFilter(sources=["orders"], change_types=[ChangeType.TYPE_CHANGED])
    results = filter_reports([r1, r2], f)
    assert len(results) == 1
    assert results[0].source == "orders"
    assert len(results[0].changes) == 1
    assert results[0].changes[0].change_type == ChangeType.TYPE_CHANGED
