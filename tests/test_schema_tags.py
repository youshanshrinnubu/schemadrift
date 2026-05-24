"""Tests for schemadrift.schema_tags."""

import pytest

from schemadrift.schema_tags import TagEntry, TagStore


@pytest.fixture
def store(tmp_path):
    return TagStore(str(tmp_path / "tags"))


def test_set_and_get_tags(store):
    entry = store.set_tags("orders", "v1", ["baseline", "prod"])
    assert entry.tags == ["baseline", "prod"]

    loaded = store.get_tags("orders", "v1")
    assert loaded is not None
    assert loaded.source == "orders"
    assert loaded.version == "v1"
    assert "baseline" in loaded.tags


def test_get_missing_version_returns_none(store):
    result = store.get_tags("orders", "v99")
    assert result is None


def test_find_by_tag_returns_matching_entries(store):
    store.set_tags("users", "v1", ["baseline"])
    store.set_tags("users", "v2", ["release", "baseline"])
    store.set_tags("users", "v3", ["release"])

    results = store.find_by_tag("users", "baseline")
    versions = [e.version for e in results]
    assert "v1" in versions
    assert "v2" in versions
    assert "v3" not in versions


def test_find_by_tag_no_matches_returns_empty(store):
    store.set_tags("payments", "v1", ["draft"])
    results = store.find_by_tag("payments", "prod")
    assert results == []


def test_list_all_returns_sorted(store):
    store.set_tags("events", "v3", ["c"])
    store.set_tags("events", "v1", ["a"])
    store.set_tags("events", "v2", ["b"])

    entries = store.list_all("events")
    assert [e.version for e in entries] == ["v1", "v2", "v3"]


def test_overwrite_tags_replaces_previous(store):
    store.set_tags("orders", "v1", ["old"])
    store.set_tags("orders", "v1", ["new", "updated"])

    loaded = store.get_tags("orders", "v1")
    assert loaded.tags == ["new", "updated"]


def test_delete_tags_removes_entry(store):
    store.set_tags("orders", "v1", ["temp"])
    removed = store.delete_tags("orders", "v1")
    assert removed is True
    assert store.get_tags("orders", "v1") is None


def test_delete_missing_returns_false(store):
    result = store.delete_tags("orders", "v999")
    assert result is False


def test_tag_entry_roundtrip():
    entry = TagEntry(source="inventory", version="v5", tags=["prod", "stable"])
    restored = TagEntry.from_dict(entry.to_dict())
    assert restored.source == entry.source
    assert restored.version == entry.version
    assert restored.tags == entry.tags


def test_sources_are_isolated(store):
    store.set_tags("source_a", "v1", ["alpha"])
    store.set_tags("source_b", "v1", ["beta"])

    a = store.get_tags("source_a", "v1")
    b = store.get_tags("source_b", "v1")
    assert a.tags == ["alpha"]
    assert b.tags == ["beta"]
