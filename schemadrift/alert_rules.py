"""Alert rules for schema drift notifications."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from schemadrift.drift_detector import ChangeType


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    name: str
    change_types: List[ChangeType]
    severity: AlertSeverity = AlertSeverity.WARNING
    sources: List[str] = field(default_factory=list)  # empty = all sources

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "change_types": [ct.value for ct in self.change_types],
            "severity": self.severity.value,
            "sources": self.sources,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlertRule":
        return cls(
            name=data["name"],
            change_types=[ChangeType(ct) for ct in data["change_types"]],
            severity=AlertSeverity(data.get("severity", "warning")),
            sources=data.get("sources", []),
        )


DEFAULT_RULES: List[AlertRule] = [
    AlertRule(
        name="column_removed",
        change_types=[ChangeType.COLUMN_REMOVED],
        severity=AlertSeverity.CRITICAL,
    ),
    AlertRule(
        name="type_changed",
        change_types=[ChangeType.TYPE_CHANGED],
        severity=AlertSeverity.WARNING,
    ),
    AlertRule(
        name="column_added",
        change_types=[ChangeType.COLUMN_ADDED],
        severity=AlertSeverity.INFO,
    ),
]
