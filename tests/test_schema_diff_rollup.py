"""Tests for schema_diff_rollup module."""

import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_diff_rollup import rollup_reports, SourceRollup, DriftRollup


def make_report(source: str, changes=None, generated_at="2024-01-01T00:00:00Z") -> DriftReport:
    return DriftReport(
        source=source,
        from_version="v1",
        to_version="v2",
        changes=changes or [],
        generated_at=generated_at,
    )


def make_change(change_type: ChangeType, column="col") -> DriftChange:
    return DriftChange(
        change_type=change_type,
        column_name=column,
        before=None,
        after=None,
    )


def test_empty_reports_returns_empty_rollup():
    rollup = rollup_reports([])
    assert rollup.sources == {}
    assert rollup.total_sources_with_drift == 0


def test_single_report_no_drift():
    report = make_report("orders")
    rollup = rollup_reports([report])
    assert "orders" in rollup.sources
    entry = rollup.sources["orders"]
    assert entry.total_reports == 1
    assert entry.reports_with_drift == 0
    assert entry.change_type_counts == {}


def test_single_report_with_drift():
    change = make_change(ChangeType.COLUMN_ADDED, "new_col")
    report = make_report("orders", changes=[change])
    rollup = rollup_reports([report])
    entry = rollup.sources["orders"]
    assert entry.reports_with_drift == 1
    assert entry.change_type_counts.get("column_added") == 1


def test_multiple_reports_same_source_aggregated():
    r1 = make_report("users", changes=[make_change(ChangeType.COLUMN_REMOVED, "old")])
    r2 = make_report("users", changes=[make_change(ChangeType.COLUMN_REMOVED, "id")])
    r3 = make_report("users", changes=[])
    rollup = rollup_reports([r1, r2, r3])
    entry = rollup.sources["users"]
    assert entry.total_reports == 3
    assert entry.reports_with_drift == 2
    assert entry.change_type_counts["column_removed"] == 2


def test_multiple_sources_tracked_separately():
    r1 = make_report("users", changes=[make_change(ChangeType.COLUMN_ADDED)])
    r2 = make_report("orders", changes=[])
    rollup = rollup_reports([r1, r2])
    assert "users" in rollup.sources
    assert "orders" in rollup.sources
    assert rollup.total_sources_with_drift == 1


def test_first_and_last_seen_tracked():
    r1 = make_report("logs", generated_at="2024-01-01T00:00:00Z")
    r2 = make_report("logs", generated_at="2024-06-15T12:00:00Z")
    r3 = make_report("logs", generated_at="2024-03-10T08:00:00Z")
    rollup = rollup_reports([r1, r2, r3])
    entry = rollup.sources["logs"]
    assert entry.first_seen == "2024-01-01T00:00:00Z"
    assert entry.last_seen == "2024-06-15T12:00:00Z"


def test_to_dict_structure():
    change = make_change(ChangeType.TYPE_CHANGED, "amount")
    report = make_report("payments", changes=[change])
    rollup = rollup_reports([report], window_start="2024-01-01", window_end="2024-12-31")
    d = rollup.to_dict()
    assert d["window_start"] == "2024-01-01"
    assert d["window_end"] == "2024-12-31"
    assert "payments" in d["sources"]
    assert d["sources"]["payments"]["reports_with_drift"] == 1
