"""Tests for SnapshotStore persistence layer."""

import os
import pytest
from datetime import datetime

from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.snapshot_store import SnapshotStore


@pytest.fixture
def store(tmp_path):
    return SnapshotStore(store_dir=str(tmp_path / ".schemadrift"))


def make_snapshot(source: str, version: str, columns=None) -> SchemaSnapshot:
    if columns is None:
        columns = [ColumnSchema(name="id", dtype="int", nullable=False)]
    return SchemaSnapshot(
        source_name=source,
        version=version,
        captured_at=datetime(2024, 1, int(version[-1]) if version[-1].isdigit() else 1),
        columns=columns,
    )


def test_save_and_load_latest(store):
    snap = make_snapshot("orders", "v1")
    store.save(snap)
    loaded = store.load_latest("orders")
    assert loaded is not None
    assert loaded.version == "v1"
    assert loaded.source_name == "orders"


def test_load_all_ordered(store):
    snap1 = make_snapshot("orders", "v1")
    snap2 = make_snapshot("orders", "v2")
    store.save(snap2)
    store.save(snap1)
    all_snaps = store.load_all("orders")
    assert len(all_snaps) == 2
    assert all_snaps[0].version == "v1"
    assert all_snaps[1].version == "v2"


def test_load_at_version(store):
    store.save(make_snapshot("users", "v1"))
    store.save(make_snapshot("users", "v2"))
    snap = store.load_at_version("users", "v2")
    assert snap is not None
    assert snap.version == "v2"


def test_load_at_version_missing(store):
    store.save(make_snapshot("users", "v1"))
    assert store.load_at_version("users", "v99") is None


def test_load_latest_empty(store):
    assert store.load_latest("nonexistent") is None


def test_list_sources(store):
    store.save(make_snapshot("orders", "v1"))
    store.save(make_snapshot("users", "v1"))
    sources = store.list_sources()
    assert "orders" in sources
    assert "users" in sources


def test_delete_source(store):
    store.save(make_snapshot("orders", "v1"))
    assert store.delete("orders") is True
    assert store.load_latest("orders") is None


def test_delete_nonexistent(store):
    assert store.delete("ghost") is False


def test_multiple_columns_roundtrip(store):
    columns = [
        ColumnSchema(name="id", dtype="int", nullable=False),
        ColumnSchema(name="email", dtype="varchar", nullable=True),
    ]
    snap = make_snapshot("accounts", "v1", columns=columns)
    store.save(snap)
    loaded = store.load_latest("accounts")
    assert len(loaded.columns) == 2
    assert loaded.columns[1].name == "email"
