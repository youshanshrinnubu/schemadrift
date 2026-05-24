"""Tests for profile_store module."""

import pytest
from schemadrift.column_profile import ColumnProfile, SchemaProfile
from schemadrift.profile_store import ProfileStore


@pytest.fixture
def store(tmp_path):
    return ProfileStore(base_dir=str(tmp_path / "profiles"))


def make_profile(source="orders", version="v1") -> SchemaProfile:
    return SchemaProfile(
        source=source,
        version=version,
        columns=[
            ColumnProfile(name="id", dtype="int", nullable=False, unique=True),
            ColumnProfile(name="total", dtype="float"),
        ],
    )


def test_save_and_load(store):
    p = make_profile()
    store.save(p)
    loaded = store.load("orders", "v1")
    assert loaded is not None
    assert loaded.source == "orders"
    assert loaded.version == "v1"
    assert len(loaded.columns) == 2


def test_load_missing_returns_none(store):
    result = store.load("nonexistent", "v99")
    assert result is None


def test_load_all_returns_ordered(store):
    for v in ["v3", "v1", "v2"]:
        store.save(make_profile(version=v))
    all_p = store.load_all("orders")
    versions = [p.version for p in all_p]
    assert versions == sorted(versions)


def test_load_latest_returns_last(store):
    for v in ["v1", "v2", "v3"]:
        store.save(make_profile(version=v))
    latest = store.load_latest("orders")
    assert latest is not None
    assert latest.version == "v3"


def test_load_latest_empty_returns_none(store):
    assert store.load_latest("ghost") is None


def test_list_versions(store):
    for v in ["v1", "v2"]:
        store.save(make_profile(version=v))
    versions = store.list_versions("orders")
    assert versions == ["v1", "v2"]


def test_list_versions_missing_source(store):
    assert store.list_versions("missing") == []


def test_delete_removes_file(store):
    store.save(make_profile(version="v1"))
    result = store.delete("orders", "v1")
    assert result is True
    assert store.load("orders", "v1") is None


def test_delete_nonexistent_returns_false(store):
    assert store.delete("orders", "v99") is False
