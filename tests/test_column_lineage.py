"""Tests for column_lineage rename detection."""

import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.column_lineage import detect_lineage_hints, LineageHint


def make_report(
    changes: list[DriftChange],
    source: str = "test_source",
    version_from: str = "v1",
    version_to: str = "v2",
) -> DriftReport:
    return DriftReport(
        source=source,
        version_from=version_from,
        version_to=version_to,
        changes=changes,
    )


def make_change(change_type: ChangeType, column: str, before=None, after=None) -> DriftChange:
    return DriftChange(change_type=change_type, column_name=column, before=before, after=after)


def test_no_hints_when_no_changes():
    report = make_report([])
    hints = detect_lineage_hints(report)
    assert hints == []


def test_no_hints_when_only_type_changes():
    report = make_report([
        make_change(ChangeType.TYPE_CHANGED, "age", before="int", after="float")
    ])
    hints = detect_lineage_hints(report)
    assert hints == []


def test_detects_rename_same_type_similar_name():
    report = make_report([
        make_change(ChangeType.COLUMN_REMOVED, "user_id", before="int"),
        make_change(ChangeType.COLUMN_ADDED, "user_key", after="int"),
    ])
    hints = detect_lineage_hints(report, min_confidence=0.5)
    assert len(hints) == 1
    assert hints[0].old_name == "user_id"
    assert hints[0].new_name == "user_key"
    assert hints[0].confidence >= 0.5


def test_no_hint_below_min_confidence():
    report = make_report([
        make_change(ChangeType.COLUMN_REMOVED, "alpha", before="int"),
        make_change(ChangeType.COLUMN_ADDED, "zzzzzzz", after="text"),
    ])
    hints = detect_lineage_hints(report, min_confidence=0.5)
    assert hints == []


def test_hints_sorted_by_confidence_descending():
    report = make_report([
        make_change(ChangeType.COLUMN_REMOVED, "col_a", before="int"),
        make_change(ChangeType.COLUMN_ADDED, "col_b", after="int"),
        make_change(ChangeType.COLUMN_REMOVED, "xyz", before="text"),
        make_change(ChangeType.COLUMN_ADDED, "abc", after="int"),
    ])
    hints = detect_lineage_hints(report, min_confidence=0.0)
    confidences = [h.confidence for h in hints]
    assert confidences == sorted(confidences, reverse=True)


def test_hint_to_dict_contains_expected_keys():
    hint = LineageHint(
        source="src",
        old_name="old_col",
        new_name="new_col",
        version_from="v1",
        version_to="v2",
        confidence=0.75,
    )
    d = hint.to_dict()
    assert d["source"] == "src"
    assert d["old_name"] == "old_col"
    assert d["new_name"] == "new_col"
    assert d["confidence"] == 0.75
