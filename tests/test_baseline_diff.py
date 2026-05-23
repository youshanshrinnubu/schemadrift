"""Tests for schemadrift.baseline_diff module."""

import pytest

from schemadrift.baseline import Baseline, BaselineStore
from schemadrift.baseline_diff import diff_against_baseline, promote_to_baseline
from schemadrift.schema_snapshot import ColumnSchema, SchemaSnapshot


TS = "2024-06-01T12:00:00"


def make_snapshot(source="db.orders", version=1, columns=None) -> SchemaSnapshot:
    if columns is None:
        columns = [
            ColumnSchema(name="id", dtype="integer", nullable=False),
            ColumnSchema(name="total", dtype="numeric", nullable=True),
        ]
    return SchemaSnapshot(source=source, version=version, captured_at=TS, columns=columns)


@pytest.fixture
def store(tmp_path):
    return BaselineStore(directory=str(tmp_path / ".schemadrift"))


def test_no_drift_when_identical(store):
    snap = make_snapshot()
    store.save(Baseline(name="prod", source="db.orders", snapshot=snap))
    result = diff_against_baseline(snap, "prod", store=store)
    assert not result.has_drift
    assert result.baseline_name == "prod"


def test_detects_added_column(store):
    base_snap = make_snapshot(version=1)
    store.save(Baseline(name="prod", source="db.orders", snapshot=base_snap))

    new_cols = base_snap.columns + [ColumnSchema(name="discount", dtype="numeric", nullable=True)]
    new_snap = make_snapshot(version=2, columns=new_cols)

    result = diff_against_baseline(new_snap, "prod", store=store)
    assert result.has_drift
    assert result.current_version == 2
    assert result.baseline_version == 1


def test_missing_baseline_raises_key_error(store):
    snap = make_snapshot()
    with pytest.raises(KeyError, match="ghost"):
        diff_against_baseline(snap, "ghost", store=store)


def test_source_mismatch_raises_value_error(store):
    base_snap = make_snapshot(source="db.orders")
    store.save(Baseline(name="prod", source="db.orders", snapshot=base_snap))
    other_snap = make_snapshot(source="db.invoices")
    with pytest.raises(ValueError, match="Source mismatch"):
        diff_against_baseline(other_snap, "prod", store=store)


def test_promote_creates_baseline(store):
    snap = make_snapshot(version=3)
    bl = promote_to_baseline(snap, "staging", store=store)
    assert bl.name == "staging"
    loaded = store.load("staging")
    assert loaded is not None
    assert loaded.snapshot.version == 3


def test_promote_overwrites_existing(store):
    snap1 = make_snapshot(version=1)
    snap2 = make_snapshot(version=5)
    promote_to_baseline(snap1, "prod", store=store)
    promote_to_baseline(snap2, "prod", store=store)
    loaded = store.load("prod")
    assert loaded.snapshot.version == 5
