import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_diff_stats import compute_drift_stats, DriftStatsReport


def make_change(name: str, change_type: ChangeType) -> DriftChange:
    return DriftChange(
        column_name=name,
        change_type=change_type,
        before="int" if change_type == ChangeType.TYPE_CHANGED else None,
        after="str" if change_type == ChangeType.TYPE_CHANGED else None,
    )


def make_report(source: str, from_v: str, to_v: str, changes) -> DriftReport:
    return DriftReport(source=source, from_version=from_v, to_version=to_v, changes=changes)


def test_empty_reports_returns_empty_stats():
    result = compute_drift_stats([])
    assert isinstance(result, DriftStatsReport)
    assert result.sources == []
    assert result.total_changes() == 0
    assert result.most_active_source() is None


def test_single_report_no_changes():
    report = make_report("db.users", "v1", "v2", [])
    result = compute_drift_stats([report])
    assert len(result.sources) == 1
    stats = result.sources[0]
    assert stats.source == "db.users"
    assert stats.total_changes == 0
    assert stats.total_versions_compared == 1
    assert stats.changes_by_type == {}


def test_single_report_with_changes():
    changes = [
        make_change("email", ChangeType.COLUMN_ADDED),
        make_change("age", ChangeType.COLUMN_REMOVED),
    ]
    report = make_report("db.users", "v1", "v2", changes)
    result = compute_drift_stats([report])
    stats = result.sources[0]
    assert stats.total_changes == 2
    assert stats.changes_by_type.get("added") == 1
    assert stats.changes_by_type.get("removed") == 1
    assert stats.most_changed_version == "v2"
    assert stats.most_changed_version_count == 2


def test_multiple_reports_same_source_aggregated():
    r1 = make_report("db.orders", "v1", "v2", [make_change("col_a", ChangeType.COLUMN_ADDED)])
    r2 = make_report("db.orders", "v2", "v3", [
        make_change("col_b", ChangeType.COLUMN_ADDED),
        make_change("col_c", ChangeType.COLUMN_REMOVED),
    ])
    result = compute_drift_stats([r1, r2])
    assert len(result.sources) == 1
    stats = result.sources[0]
    assert stats.total_versions_compared == 2
    assert stats.total_changes == 3
    assert stats.most_changed_version == "v3"
    assert stats.most_changed_version_count == 2


def test_multiple_sources_separated():
    r1 = make_report("src_a", "v1", "v2", [make_change("x", ChangeType.COLUMN_ADDED)])
    r2 = make_report("src_b", "v1", "v2", [])
    result = compute_drift_stats([r1, r2])
    assert len(result.sources) == 2
    assert result.total_changes() == 1
    assert result.most_active_source() == "src_a"


def test_to_dict_structure():
    changes = [make_change("id", ChangeType.TYPE_CHANGED)]
    report = make_report("db.events", "v1", "v2", changes)
    result = compute_drift_stats([report])
    d = result.to_dict()
    assert "sources" in d
    assert len(d["sources"]) == 1
    src = d["sources"][0]
    assert src["source"] == "db.events"
    assert src["total_changes"] == 1
    assert "type_changed" in src["changes_by_type"]
