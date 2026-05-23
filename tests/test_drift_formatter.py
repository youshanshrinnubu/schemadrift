"""Tests for schemadrift.drift_formatter."""

import json
import pytest

from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.drift_formatter import format_report, OutputFormat


def make_report(changes=None):
    return DriftReport(
        source_name="orders",
        from_version=1,
        to_version=2,
        changes=changes or [],
    )


def make_change(change_type=ChangeType.COLUMN_ADDED, column="email", old=None, new="varchar"):
    return DriftChange(
        change_type=change_type,
        column_name=column,
        old_value=old,
        new_value=new,
    )


# --- TEXT format ---

def test_text_no_drift():
    report = make_report()
    output = format_report(report, OutputFormat.TEXT)
    assert "No drift detected" in output
    assert "orders" in output


def test_text_with_changes():
    report = make_report([make_change()])
    output = format_report(report, OutputFormat.TEXT)
    assert "Drift detected" in output
    assert "email" in output
    assert "column_added" in output
    assert "1 change" in output


def test_text_type_changed_shows_before_after():
    change = make_change(ChangeType.TYPE_CHANGED, "amount", old="int", new="float")
    output = format_report(make_report([change]), OutputFormat.TEXT)
    assert "before: int" in output
    assert "after:  float" in output


# --- MARKDOWN format ---

def test_markdown_no_drift():
    output = format_report(make_report(), OutputFormat.MARKDOWN)
    assert "No changes detected" in output
    assert "##" in output


def test_markdown_has_table_header():
    report = make_report([make_change()])
    output = format_report(report, OutputFormat.MARKDOWN)
    assert "| Column |" in output
    assert "`email`" in output


# --- JSON format ---

def test_json_output_is_valid():
    report = make_report([make_change()])
    output = format_report(report, OutputFormat.JSON)
    data = json.loads(output)
    assert data["source_name"] == "orders"
    assert data["from_version"] == 1
    assert len(data["changes"]) == 1


def test_json_no_drift_empty_changes():
    output = format_report(make_report(), OutputFormat.JSON)
    data = json.loads(output)
    assert data["changes"] == []


# --- default format ---

def test_default_format_is_text():
    report = make_report()
    assert format_report(report) == format_report(report, OutputFormat.TEXT)
