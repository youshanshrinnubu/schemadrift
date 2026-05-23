"""Tests for alert_formatter."""
import pytest
from schemadrift.drift_detector import DriftChange, ChangeType
from schemadrift.alert_rules import AlertSeverity
from schemadrift.alert_engine import Alert
from schemadrift.alert_formatter import format_alerts, format_alerts_text, format_alerts_markdown


def make_alert(severity=AlertSeverity.WARNING, column="age", change_type=ChangeType.TYPE_CHANGED):
    return Alert(
        rule_name="type_changed",
        severity=severity,
        source="db.users",
        version="v2",
        change=DriftChange(column=column, change_type=change_type, before="int", after="str"),
    )


def test_text_no_alerts():
    result = format_alerts_text([])
    assert "No alerts" in result


def test_text_with_alert_contains_severity():
    alert = make_alert(severity=AlertSeverity.CRITICAL, change_type=ChangeType.COLUMN_REMOVED)
    result = format_alerts_text([alert])
    assert "CRITICAL" in result
    assert "db.users" in result


def test_markdown_no_alerts():
    result = format_alerts_markdown([])
    assert "No alerts" in result
    assert "##" in result


def test_markdown_with_alert_contains_table():
    alert = make_alert()
    result = format_alerts_markdown([alert])
    assert "|" in result
    assert "db.users" in result
    assert "warning" in result


def test_format_alerts_default_is_text():
    result = format_alerts([])
    assert "No alerts" in result


def test_format_alerts_markdown_dispatch():
    result = format_alerts([], fmt="markdown")
    assert "##" in result


def test_alerts_sorted_critical_first():
    alerts = [
        make_alert(severity=AlertSeverity.INFO, change_type=ChangeType.COLUMN_ADDED),
        make_alert(severity=AlertSeverity.CRITICAL, change_type=ChangeType.COLUMN_REMOVED),
        make_alert(severity=AlertSeverity.WARNING, change_type=ChangeType.TYPE_CHANGED),
    ]
    result = format_alerts_text(alerts)
    critical_pos = result.index("CRITICAL")
    warning_pos = result.index("WARNING")
    info_pos = result.index("INFO")
    assert critical_pos < warning_pos < info_pos
