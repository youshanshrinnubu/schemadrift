"""Tests for schemadrift.baseline module."""

import pytest

from schemadrift.baseline import Baseline, BaselineStore
from schemadrift.schema_snapshot import ColumnSchema, SchemaSnapshot


DEFAULT_TS = "2024-01-01T00:00:00"


def make_snapshot(source: str = "db.users", version: int = 1) -> SchemaSnapshot:
    return SchemaSnapshot(
        source=source,
        version=version,
        captured_at=DEFAULT_TS,
        columns=[
            ColumnSchema(name="id", dtype="integer", nullable=False),
            ColumnSchema(name="email", dtype="varchar", nullable=False),
        ],
    )


@pytest.fixture
def store(tmp_path):
    return BaselineStore(directory=str(tmp_path / ".schemadrift"))


def test_save_and_load_baseline(store):
    snap = make_snapshot()
    bl = Baseline(name="production", source="db.users", snapshot=snap)
    store.save(bl)
    loaded = store.load("production")
    assert loaded is not None
    assert loaded.name == "production"
    assert loaded.source == "db.users"
    assert len(loaded.snapshot.columns) == 2


def test_load_missing_returns_none(store):
    assert store.load("nonexistent") is None


def test_list_names_empty(store):
    assert store.list_names() == []


def test_list_names_multiple(store):
    for name in ("beta", "alpha", "gamma"):
        bl = Baseline(name=name, source="db.t", snapshot=make_snapshot())
        store.save(bl)
    assert store.list_names() == ["alpha", "beta", "gamma"]


def test_overwrite_baseline(store):
    snap1 = make_snapshot(version=1)
    snap2 = make_snapshot(version=2)
    store.save(Baseline(name="prod", source="db.users", snapshot=snap1))
    store.save(Baseline(name="prod", source="db.users", snapshot=snap2))
    loaded = store.load("prod")
    assert loaded.snapshot.version == 2


def test_delete_existing(store):
    bl = Baseline(name="old", source="db.t", snapshot=make_snapshot())
    store.save(bl)
    assert store.delete("old") is True
    assert store.load("old") is None


def test_delete_missing_returns_false(store):
    assert store.delete("ghost") is False


def test_baseline_roundtrip_dict():
    snap = make_snapshot()
    bl = Baseline(name="v1", source="db.orders", snapshot=snap)
    restored = Baseline.from_dict(bl.to_dict())
    assert restored.name == bl.name
    assert restored.source == bl.source
    assert restored.snapshot.columns == bl.snapshot.columns
