"""Tests for schema_validator module."""

import pytest

from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_validator import (
    validate_snapshot,
    Violation,
    ViolationLevel,
    BUILTIN_RULES,
    ValidationReport,
)


def make_snapshot(columns: list, source: str = "test_src", version: str = "v1") -> SchemaSnapshot:
    return SchemaSnapshot(
        source=source,
        version=version,
        columns=[ColumnSchema(name=c[0], col_type=c[1]) for c in columns],
    )


def test_valid_snapshot_has_no_violations():
    snap = make_snapshot([("id", "integer"), ("name", "text")])
    report = validate_snapshot(snap)
    assert not report.violations
    assert not report.has_errors
    assert not report.has_warnings


def test_empty_schema_produces_error():
    snap = make_snapshot([])
    report = validate_snapshot(snap)
    assert report.has_errors
    names = [v.rule_name for v in report.violations]
    assert "no_empty_schema" in names


def test_unnamed_column_produces_error():
    snap = make_snapshot([("id", "integer"), ("", "text")])
    report = validate_snapshot(snap)
    assert report.has_errors
    errors = [v for v in report.violations if v.rule_name == "no_unnamed_columns"]
    assert len(errors) == 1
    assert errors[0].level == ViolationLevel.ERROR


def test_untyped_column_produces_warning():
    snap = make_snapshot([("id", "integer"), ("notes", "")])
    report = validate_snapshot(snap)
    assert not report.has_errors
    assert report.has_warnings
    warnings = [v for v in report.violations if v.rule_name == "no_untyped_columns"]
    assert len(warnings) == 1
    assert warnings[0].column == "notes"


def test_multiple_violations_accumulate():
    snap = make_snapshot([("id", ""), ("", "")])
    report = validate_snapshot(snap)
    assert len(report.violations) >= 2


def test_to_dict_structure():
    snap = make_snapshot([("id", "integer")])
    report = validate_snapshot(snap)
    d = report.to_dict()
    assert "source" in d
    assert "version" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)


def test_custom_rules_override_defaults():
    from schemadrift.schema_validator import ValidationRule
    custom = [ValidationRule("no_empty_schema", "Must have columns.", ViolationLevel.ERROR)]
    snap = make_snapshot([])
    report = validate_snapshot(snap, rules=custom)
    assert len(report.violations) == 1
    assert report.violations[0].rule_name == "no_empty_schema"


def test_report_source_and_version_match_snapshot():
    snap = make_snapshot([("x", "float")], source="my_db", version="2024-01")
    report = validate_snapshot(snap)
    assert report.source == "my_db"
    assert report.version == "2024-01"
