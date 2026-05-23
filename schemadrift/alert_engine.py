"""Evaluates drift reports against alert rules and produces alerts."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from schemadrift.alert_rules import AlertRule, AlertSeverity, DEFAULT_RULES
from schemadrift.drift_detector import DriftReport, DriftChange


@dataclass
class Alert:
    rule_name: str
    severity: AlertSeverity
    source: str
    version: str
    change: DriftChange

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "source": self.source,
            "version": self.version,
            "change": self.change.to_dict(),
        }

    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.rule_name}: "
            f"{self.source}@{self.version} — {self.change.column} "
            f"({self.change.change_type.value})"
        )


def evaluate_report(
    report: DriftReport,
    rules: Optional[List[AlertRule]] = None,
) -> List[Alert]:
    """Return alerts triggered by a drift report against the given rules."""
    if rules is None:
        rules = DEFAULT_RULES

    alerts: List[Alert] = []
    for change in report.changes:
        for rule in rules:
            if rule.sources and report.source not in rule.sources:
                continue
            if change.change_type in rule.change_types:
                alerts.append(
                    Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        source=report.source,
                        version=report.new_version,
                        change=change,
                    )
                )
    return alerts


def evaluate_reports(
    reports: List[DriftReport],
    rules: Optional[List[AlertRule]] = None,
) -> List[Alert]:
    """Evaluate multiple drift reports and aggregate all alerts."""
    all_alerts: List[Alert] = []
    for report in reports:
        all_alerts.extend(evaluate_report(report, rules=rules))
    return all_alerts
