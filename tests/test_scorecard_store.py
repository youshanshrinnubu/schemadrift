import pytest
import os
from schemadrift.schema_diff_scorecard import DriftScorecard, ScorecardEntry
from schemadrift.scorecard_store import ScorecardStore


@pytest.fixture
def store(tmp_path):
    return ScorecardStore(str(tmp_path / "scorecards"))


def make_entry(source: str = "orders", health: float = 0.9) -> ScorecardEntry:
    return ScorecardEntry(
        source=source,
        total_versions=5,
        versions_with_drift=1,
        total_changes=2,
        added=1,
        removed=0,
        type_changed=1,
        drift_rate=0.2,
        health_score=health,
    )


def make_scorecard(*sources) -> DriftScorecard:
    entries = [make_entry(s) for s in sources]
    return DriftScorecard(entries=entries)


def test_save_and_load_roundtrip(store):
    sc = make_scorecard("users", "events")
    store.save("2024-01-01", sc)
    loaded = store.load("2024-01-01")
    assert loaded is not None
    assert len(loaded.entries) == 2
    sources = {e.source for e in loaded.entries}
    assert sources == {"users", "events"}


def test_load_missing_returns_none(store):
    assert store.load("nonexistent") is None


def test_list_versions_empty(store):
    assert store.list_versions() == []


def test_list_versions_returns_sorted(store):
    store.save("2024-03-01", make_scorecard("a"))
    store.save("2024-01-01", make_scorecard("b"))
    store.save("2024-02-01", make_scorecard("c"))
    versions = store.list_versions()
    assert versions == sorted(versions)


def test_load_latest_returns_last(store):
    store.save("2024-01-01", make_scorecard("old"))
    store.save("2024-06-01", make_scorecard("new"))
    latest = store.load_latest()
    assert latest is not None
    assert latest.entries[0].source == "new"


def test_load_latest_empty_store_returns_none(store):
    assert store.load_latest() is None


def test_entry_fields_preserved(store):
    entry = make_entry("payments", health=0.75)
    sc = DriftScorecard(entries=[entry])
    store.save("v1", sc)
    loaded = store.load("v1")
    e = loaded.entries[0]
    assert e.health_score == 0.75
    assert e.drift_rate == 0.2
    assert e.removed == 0
    assert e.type_changed == 1
