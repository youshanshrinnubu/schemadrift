"""Tests for schema_diff_digest.py"""

import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_diff_digest import build_digest, DigestEntry, DriftDigest


def make_change(change_type: ChangeType, column: str = "col") -> DriftChange:
    return DriftChange(
        change_type=change_type,
        column_name=column,
        before=None,
        after=None,
    )


def make_report(
    source: str = "db.table",
    from_version: str = "v1",
    to_version: str = "v2",
    changes=None,
    timestamp: str = "2024-01-01T00:00:00",
) -> DriftReport:
    return DriftReport(
        source=source,
        from_version=from_version,
        to_version=to_version,
        changes=changes or [],
        timestamp=timestamp,
    )


def test_empty_reports_returns_empty_digest():
    digest = build_digest({})
    assert digest.total_sources == 0
    assert digest.sources_with_drift == 0
    assert digest.entries == []


def test_single_source_no_changes():
    reports = {"db.table": [make_report(changes=[])]}
    digest = build_digest(reports)
    assert digest.total_sources == 1
    assert digest.sources_with_drift == 0
    assert len(digest.entries) == 1
    entry = digest.entries[0]
    assert entry.source == "db.table"
    assert entry.total_changes == 0


def test_single_source_with_added_column():
    reports = {
        "db.table": [
            make_report(changes=[make_change(ChangeType.COLUMN_ADDED, "new_col")])
        ]
    }
    digest = build_digest(reports)
    assert digest.sources_with_drift == 1
    entry = digest.entries[0]
    assert entry.added == 1
    assert entry.removed == 0
    assert entry.total_changes == 1


def test_multiple_change_types_counted_correctly():
    reports = {
        "src": [
            make_report(changes=[
                make_change(ChangeType.COLUMN_ADDED, "a"),
                make_change(ChangeType.COLUMN_REMOVED, "b"),
                make_change(ChangeType.TYPE_CHANGED, "c"),
                make_change(ChangeType.NULLABLE_CHANGED, "d"),
            ])
        ]
    }
    digest = build_digest(reports)
    entry = digest.entries[0]
    assert entry.added == 1
    assert entry.removed == 1
    assert entry.type_changed == 1
    assert entry.nullable_changed == 1
    assert entry.total_changes == 4


def test_multiple_sources_sorted_alphabetically():
    reports = {
        "zzz": [make_report(source="zzz")],
        "aaa": [make_report(source="aaa")],
    }
    digest = build_digest(reports)
    assert digest.entries[0].source == "aaa"
    assert digest.entries[1].source == "zzz"


def test_to_dict_contains_expected_keys():
    reports = {"db.table": [make_report()]}
    digest = build_digest(reports)
    d = digest.to_dict()
    assert "generated_at" in d
    assert "total_sources" in d
    assert "sources_with_drift" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_timestamps_captured_in_entry():
    reports = {
        "src": [
            make_report(from_version="v1", to_version="v2", timestamp="2024-01-01T00:00:00"),
            make_report(from_version="v2", to_version="v3", timestamp="2024-06-01T00:00:00"),
        ]
    }
    digest = build_digest(reports)
    entry = digest.entries[0]
    assert entry.first_seen == "2024-01-01T00:00:00"
    assert entry.last_seen == "2024-06-01T00:00:00"
