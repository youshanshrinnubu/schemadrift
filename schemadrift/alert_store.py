"""Persistence layer for alerts — save and load alerts by source and version."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from schemadrift.alert_engine import Alert
from schemadrift.alert_rules import AlertSeverity


class AlertStore:
    """Stores and retrieves fired alerts on disk as JSON."""

    def __init__(self, base_dir: str = ".schemadrift/alerts") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _source_path(self, source_name: str) -> Path:
        safe = source_name.replace("/", "__")
        path = self.base_dir / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, source_name: str, version: str, alerts: List[Alert]) -> None:
        """Persist alerts for a given source and version."""
        path = self._source_path(source_name) / f"{version}.json"
        data = [a.to_dict() for a in alerts]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def load(self, source_name: str, version: str) -> Optional[List[Alert]]:
        """Load alerts for a specific version, or None if not found."""
        path = self._source_path(source_name) / f"{version}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return [_alert_from_dict(d) for d in data]

    def load_all(self, source_name: str) -> List[tuple[str, List[Alert]]]:
        """Return all (version, alerts) pairs for a source, sorted by version."""
        source_path = self._source_path(source_name)
        results = []
        for entry in sorted(source_path.iterdir()):
            if entry.suffix == ".json":
                version = entry.stem
                alerts = self.load(source_name, version)
                if alerts is not None:
                    results.append((version, alerts))
        return results

    def list_sources(self) -> List[str]:
        """Return all source names that have stored alerts."""
        return [
            p.name.replace("__", "/")
            for p in sorted(self.base_dir.iterdir())
            if p.is_dir()
        ]


def _alert_from_dict(d: dict) -> Alert:
    from schemadrift.alert_rules import AlertRule, AlertSeverity
    from schemadrift.drift_detector import ChangeType

    rule = AlertRule(
        change_type=ChangeType(d["rule"]["change_type"]),
        severity=AlertSeverity(d["rule"]["severity"]),
        message_template=d["rule"]["message_template"],
    )
    return Alert(
        rule=rule,
        source_name=d["source_name"],
        version=d["version"],
        column=d["column"],
        detail=d["detail"],
    )
