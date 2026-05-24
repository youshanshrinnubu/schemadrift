"""Tests for schema_watchlist module."""

import pytest
from pathlib import Path
from schemadrift.schema_watchlist import WatchEntry, Watchlist, WatchlistStore


@pytest.fixture
def store(tmp_path):
    return WatchlistStore(str(tmp_path))


def test_add_source_watch():
    wl = Watchlist()
    wl.add("orders", reason="critical table")
    assert len(wl.entries) == 1
    assert wl.entries[0].source == "orders"
    assert wl.entries[0].column is None


def test_add_column_watch():
    wl = Watchlist()
    wl.add("orders", column="total_amount", reason="billing")
    assert wl.entries[0].column == "total_amount"


def test_no_duplicate_entries():
    wl = Watchlist()
    wl.add("orders")
    wl.add("orders")
    assert len(wl.entries) == 1


def test_is_watched_exact_match():
    wl = Watchlist()
    wl.add("orders", column="id")
    assert wl.is_watched("orders", column="id")
    assert not wl.is_watched("orders", column="name")


def test_is_watched_source_level_covers_columns():
    wl = Watchlist()
    wl.add("orders")  # watch entire source
    assert wl.is_watched("orders", column="any_column")


def test_remove_entry_returns_true():
    wl = Watchlist()
    wl.add("orders")
    result = wl.remove("orders")
    assert result is True
    assert len(wl.entries) == 0


def test_remove_missing_returns_false():
    wl = Watchlist()
    result = wl.remove("nonexistent")
    assert result is False


def test_sources_returns_unique_sorted():
    wl = Watchlist()
    wl.add("users", column="email")
    wl.add("orders")
    wl.add("users", column="name")
    assert wl.sources() == ["orders", "users"]


def test_roundtrip_serialization():
    wl = Watchlist()
    wl.add("products", column="price", reason="revenue")
    wl.add("orders")
    restored = Watchlist.from_dict(wl.to_dict())
    assert len(restored.entries) == 2
    assert restored.entries[0].column == "price"


def test_store_save_and_load(store):
    wl = Watchlist()
    wl.add("events", reason="analytics")
    store.save(wl)
    loaded = store.load()
    assert len(loaded.entries) == 1
    assert loaded.entries[0].source == "events"


def test_store_load_missing_returns_empty(store):
    wl = store.load()
    assert isinstance(wl, Watchlist)
    assert wl.entries == []


def test_store_overwrite(store):
    wl = Watchlist()
    wl.add("a")
    store.save(wl)
    wl.add("b")
    store.save(wl)
    loaded = store.load()
    assert len(loaded.entries) == 2
