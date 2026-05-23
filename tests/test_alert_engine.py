"""Tests for alert_engine and alert_rules."""
import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.alert_rules import AlertRule, AlertSeverity, DEFAULT_RULES
from schemadrift.alert_engine import Alert, evaluate_report, evaluate_reports


def make_report(source="db.users", old="v1", new="v2", changes=None):
    return DriftReport(
        source=source,
        old_version=old,
        new_version=new,
        changes=changes or [],
    )


def make_change(column="email", change_type=ChangeType.COLUMN_ADDED, before=None, after=None):
    return DriftChange(column=column, change_type=change_type, before=before, after=after)


def test_no_alerts_when_no_changes():
    report = make_report(changes=[])
    alerts = evaluate_report(report)
    assert alerts == []


def test_column_removed_triggers_critical():
    report = make_report(changes=[make_change(change_type=ChangeType.COLUMN_REMOVED)])
    alerts = evaluate_report(report)
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.CRITICAL
    assert alerts[0].rule_name == "column_removed"


def test_type_changed_triggers_warning():
    report = make_report(changes=[make_change(change_type=ChangeType.TYPE_CHANGED, before="int", after="str")])
    alerts = evaluate_report(report)
    assert any(a.severity == AlertSeverity.WARNING for a in alerts)


def test_column_added_triggers_info():
    report = make_report(changes=[make_change(change_type=ChangeType.COLUMN_ADDED)])
    alerts = evaluate_report(report)
    assert any(a.severity == AlertSeverity.INFO for a in alerts)


def test_source_filter_excludes_non_matching():
    rule = AlertRule(
        name="only_orders",
        change_types=[ChangeType.COLUMN_ADDED],
        severity=AlertSeverity.WARNING,
        sources=["db.orders"],
    )
    report = make_report(source="db.users", changes=[make_change(change_type=ChangeType.COLUMN_ADDED)])
    alerts = evaluate_report(report, rules=[rule])
    assert alerts == []


def test_source_filter_includes_matching():
    rule = AlertRule(
        name="only_orders",
        change_types=[ChangeType.COLUMN_ADDED],
        severity=AlertSeverity.WARNING,
        sources=["db.orders"],
    )
    report = make_report(source="db.orders", changes=[make_change(change_type=ChangeType.COLUMN_ADDED)])
    alerts = evaluate_report(report, rules=[rule])
    assert len(alerts) == 1


def test_evaluate_reports_aggregates_multiple():
    reports = [
        make_report(source="db.users", changes=[make_change(change_type=ChangeType.COLUMN_REMOVED)]),
        make_report(source="db.orders", changes=[make_change(change_type=ChangeType.COLUMN_ADDED)]),
    ]
    alerts = evaluate_reports(reports)
    assert len(alerts) == 2


def test_alert_to_dict_has_expected_keys():
    report = make_report(changes=[make_change(change_type=ChangeType.COLUMN_ADDED)])
    alerts = evaluate_report(report)
    d = alerts[0].to_dict()
    assert "rule_name" in d
    assert "severity" in d
    assert "source" in d
    assert "change" in d
