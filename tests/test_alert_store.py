"""Tests for AlertStore persistence."""

from __future__ import annotations

import pytest

from schemadrift.alert_engine import Alert
from schemadrift.alert_rules import AlertRule, AlertSeverity
from schemadrift.alert_store import AlertStore
from schemadrift.drift_detector import ChangeType


@pytest.fixture
def store(tmp_path):
    return AlertStore(base_dir=str(tmp_path / "alerts"))


def make_alert(
    source: str = "db.users",
    version: str = "v2",
    column: str = "email",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    severity: AlertSeverity = AlertSeverity.CRITICAL,
) -> Alert:
    rule = AlertRule(
        change_type=change_type,
        severity=severity,
        message_template="Column '{column}' was {change_type}.",
    )
    return Alert(rule=rule, source_name=source, version=version, column=column, detail="")


def test_save_and_load_returns_same_alerts(store):
    alerts = [make_alert()]
    store.save("db.users", "v2", alerts)
    loaded = store.load("db.users", "v2")
    assert loaded is not None
    assert len(loaded) == 1
    assert loaded[0].column == "email"
    assert loaded[0].source_name == "db.users"


def test_load_missing_version_returns_none(store):
    result = store.load("db.users", "v99")
    assert result is None


def test_load_all_returns_sorted_versions(store):
    store.save("db.orders", "v1", [make_alert(source="db.orders", version="v1")])
    store.save("db.orders", "v3", [make_alert(source="db.orders", version="v3")])
    store.save("db.orders", "v2", [make_alert(source="db.orders", version="v2")])

    pairs = store.load_all("db.orders")
    versions = [v for v, _ in pairs]
    assert versions == sorted(versions)
    assert len(pairs) == 3


def test_list_sources_empty(store):
    assert store.list_sources() == []


def test_list_sources_after_save(store):
    store.save("src_a", "v1", [make_alert(source="src_a")])
    store.save("src_b", "v1", [make_alert(source="src_b")])
    sources = store.list_sources()
    assert "src_a" in sources
    assert "src_b" in sources


def test_save_empty_alerts_list(store):
    store.save("db.empty", "v1", [])
    loaded = store.load("db.empty", "v1")
    assert loaded == []


def test_severity_roundtrip(store):
    alert = make_alert(severity=AlertSeverity.WARNING, change_type=ChangeType.TYPE_CHANGED)
    store.save("db.test", "v1", [alert])
    loaded = store.load("db.test", "v1")
    assert loaded[0].rule.severity == AlertSeverity.WARNING
    assert loaded[0].rule.change_type == ChangeType.TYPE_CHANGED
