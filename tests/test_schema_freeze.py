"""Tests for schema freeze/unfreeze functionality."""

import pytest

from schemadrift.schema_freeze import FreezeStore, FreezeEntry


@pytest.fixture
def store(tmp_path):
    return FreezeStore(str(tmp_path / "freezes"))


def test_freeze_creates_entry(store):
    entry = store.freeze("orders", "v1", frozen_by="alice", reason="stable release")
    assert entry.source == "orders"
    assert entry.version == "v1"
    assert entry.frozen_by == "alice"
    assert entry.reason == "stable release"
    assert entry.frozen_at != ""


def test_is_frozen_returns_true_after_freeze(store):
    store.freeze("orders", "v1", frozen_by="alice")
    assert store.is_frozen("orders", "v1") is True


def test_is_frozen_returns_false_for_unknown_version(store):
    store.freeze("orders", "v1", frozen_by="alice")
    assert store.is_frozen("orders", "v2") is False


def test_is_frozen_returns_false_for_unknown_source(store):
    assert store.is_frozen("unknown_source", "v1") is False


def test_unfreeze_removes_entry(store):
    store.freeze("orders", "v1", frozen_by="alice")
    result = store.unfreeze("orders", "v1")
    assert result is True
    assert store.is_frozen("orders", "v1") is False


def test_unfreeze_returns_false_when_not_frozen(store):
    result = store.unfreeze("orders", "v99")
    assert result is False


def test_list_frozen_returns_all_entries(store):
    store.freeze("orders", "v1", frozen_by="alice")
    store.freeze("orders", "v2", frozen_by="bob", reason="hotfix")
    entries = store.list_frozen("orders")
    assert len(entries) == 2
    versions = {e.version for e in entries}
    assert versions == {"v1", "v2"}


def test_list_frozen_empty_for_new_source(store):
    assert store.list_frozen("nonexistent") == []


def test_freeze_entry_roundtrip():
    entry = FreezeEntry(
        source="payments",
        version="v3",
        frozen_at="2024-01-01T00:00:00+00:00",
        frozen_by="ci-bot",
        reason="post-migration lock",
    )
    restored = FreezeEntry.from_dict(entry.to_dict())
    assert restored.source == entry.source
    assert restored.version == entry.version
    assert restored.frozen_by == entry.frozen_by
    assert restored.reason == entry.reason


def test_multiple_sources_are_independent(store):
    store.freeze("orders", "v1", frozen_by="alice")
    store.freeze("users", "v1", frozen_by="bob")
    assert store.is_frozen("orders", "v1") is True
    assert store.is_frozen("users", "v1") is True
    store.unfreeze("orders", "v1")
    assert store.is_frozen("orders", "v1") is False
    assert store.is_frozen("users", "v1") is True
