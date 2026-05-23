"""Formats alert lists for display or export."""
from __future__ import annotations
from typing import List

from schemadrift.alert_engine import Alert
from schemadrift.alert_rules import AlertSeverity

_SEVERITY_ORDER = {
    AlertSeverity.CRITICAL: 0,
    AlertSeverity.WARNING: 1,
    AlertSeverity.INFO: 2,
}


def format_alerts_text(alerts: List[Alert]) -> str:
    if not alerts:
        return "No alerts triggered.\n"
    sorted_alerts = sorted(alerts, key=lambda a: _SEVERITY_ORDER[a.severity])
    lines = ["Schema Drift Alerts", "=" * 40]
    for alert in sorted_alerts:
        lines.append(str(alert))
    lines.append("")
    return "\n".join(lines)


def format_alerts_markdown(alerts: List[Alert]) -> str:
    if not alerts:
        return "## Schema Drift Alerts\n\nNo alerts triggered.\n"
    sorted_alerts = sorted(alerts, key=lambda a: _SEVERITY_ORDER[a.severity])
    lines = ["## Schema Drift Alerts", ""]
    lines.append("| Severity | Rule | Source | Version | Column | Change |")
    lines.append("|---|---|---|---|---|---|")
    for alert in sorted_alerts:
        lines.append(
            f"| {alert.severity.value} "
            f"| {alert.rule_name} "
            f"| {alert.source} "
            f"| {alert.version} "
            f"| {alert.change.column} "
            f"| {alert.change.change_type.value} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_alerts(alerts: List[Alert], fmt: str = "text") -> str:
    if fmt == "markdown":
        return format_alerts_markdown(alerts)
    return format_alerts_text(alerts)
