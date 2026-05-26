import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_diff_scorecard import (
    build_scorecard,
    ScorecardEntry,
    DriftScorecard,
    _compute_health,
)


def make_change(change_type: ChangeType, col: str = "col") -> DriftChange:
    return DriftChange(change_type=change_type, column_name=col, before=None, after=None)


def make_report(changes=None) -> DriftReport:
    return DriftReport(source="src", from_version="v1", to_version="v2", changes=changes or [])


def test_empty_reports_returns_empty_scorecard():
    scorecard = build_scorecard({})
    assert scorecard.entries == []


def test_single_source_no_drift():
    reports = {"orders": [make_report([])]}
    sc = build_scorecard(reports)
    assert len(sc.entries) == 1
    e = sc.entries[0]
    assert e.source == "orders"
    assert e.versions_with_drift == 0
    assert e.drift_rate == 0.0
    assert e.health_score == 1.0


def test_single_source_with_added_column():
    reports = {"users": [make_report([make_change(ChangeType.ADDED, "email")])]}
    sc = build_scorecard(reports)
    e = sc.entries[0]
    assert e.added == 1
    assert e.removed == 0
    assert e.versions_with_drift == 1
    assert e.drift_rate == 1.0


def test_removed_columns_reduce_health():
    changes = [make_change(ChangeType.REMOVED, "legacy_col")]
    reports = {"events": [make_report(changes)]}
    sc = build_scorecard(reports)
    e = sc.entries[0]
    assert e.removed == 1
    assert e.health_score < 1.0


def test_multiple_sources_aggregated():
    reports = {
        "a": [make_report([]), make_report([make_change(ChangeType.ADDED)])],
        "b": [make_report([make_change(ChangeType.REMOVED)])],
    }
    sc = build_scorecard(reports)
    assert len(sc.entries) == 2
    sources = {e.source for e in sc.entries}
    assert sources == {"a", "b"}


def test_top_healthy_returns_sorted():
    reports = {
        "clean": [make_report([])],
        "messy": [make_report([make_change(ChangeType.REMOVED)])],
    }
    sc = build_scorecard(reports)
    top = sc.top_healthy(2)
    assert top[0].source == "clean"


def test_top_drifting_returns_sorted():
    reports = {
        "clean": [make_report([])],
        "messy": [make_report([make_change(ChangeType.TYPE_CHANGED)])],
    }
    sc = build_scorecard(reports)
    top = sc.top_drifting(2)
    assert top[0].source == "messy"


def test_scorecard_to_dict_has_entries_key():
    sc = DriftScorecard(entries=[])
    d = sc.to_dict()
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_compute_health_perfect():
    assert _compute_health(0.0, 0, 0) == 1.0


def test_compute_health_penalises_removals():
    h_no_removal = _compute_health(0.5, 0, 1)
    h_with_removal = _compute_health(0.5, 3, 3)
    assert h_with_removal < h_no_removal
