"""Tests for column_profile module."""

import pytest
from schemadrift.column_profile import ColumnProfile, SchemaProfile, diff_profiles


def make_profile(source="orders", version="v1", columns=None) -> SchemaProfile:
    if columns is None:
        columns = [
            ColumnProfile(name="id", dtype="int", nullable=False, unique=True),
            ColumnProfile(name="amount", dtype="float", nullable=True, unique=False, default="0.0"),
        ]
    return SchemaProfile(source=source, version=version, columns=columns)


def test_column_profile_roundtrip():
    col = ColumnProfile(name="id", dtype="int", nullable=False, unique=True, default=None)
    assert ColumnProfile.from_dict(col.to_dict()) == col


def test_schema_profile_roundtrip():
    profile = make_profile()
    restored = SchemaProfile.from_dict(profile.to_dict())
    assert restored.source == profile.source
    assert restored.version == profile.version
    assert len(restored.columns) == len(profile.columns)


def test_column_map_keys():
    profile = make_profile()
    cmap = profile.column_map()
    assert set(cmap.keys()) == {"id", "amount"}


def test_diff_profiles_no_changes():
    old = make_profile(version="v1")
    new = make_profile(version="v2")
    changes = diff_profiles(old, new)
    assert changes == []


def test_diff_profiles_nullable_changed():
    old_cols = [ColumnProfile(name="amount", dtype="float", nullable=True)]
    new_cols = [ColumnProfile(name="amount", dtype="float", nullable=False)]
    old = SchemaProfile(source="s", version="v1", columns=old_cols)
    new = SchemaProfile(source="s", version="v2", columns=new_cols)
    changes = diff_profiles(old, new)
    assert len(changes) == 1
    assert changes[0]["column"] == "amount"
    assert changes[0]["attribute"] == "nullable"
    assert changes[0]["before"] is True
    assert changes[0]["after"] is False


def test_diff_profiles_default_changed():
    old_cols = [ColumnProfile(name="score", dtype="int", default=None)]
    new_cols = [ColumnProfile(name="score", dtype="int", default="0")]
    old = SchemaProfile(source="s", version="v1", columns=old_cols)
    new = SchemaProfile(source="s", version="v2", columns=new_cols)
    changes = diff_profiles(old, new)
    assert any(c["attribute"] == "default" for c in changes)


def test_diff_profiles_ignores_new_columns():
    old_cols = [ColumnProfile(name="id", dtype="int")]
    new_cols = [
        ColumnProfile(name="id", dtype="int"),
        ColumnProfile(name="new_col", dtype="str"),
    ]
    old = SchemaProfile(source="s", version="v1", columns=old_cols)
    new = SchemaProfile(source="s", version="v2", columns=new_cols)
    changes = diff_profiles(old, new)
    assert changes == []


def test_diff_profiles_multiple_attributes():
    old_cols = [ColumnProfile(name="x", dtype="int", nullable=True, unique=False)]
    new_cols = [ColumnProfile(name="x", dtype="int", nullable=False, unique=True)]
    old = SchemaProfile(source="s", version="v1", columns=old_cols)
    new = SchemaProfile(source="s", version="v2", columns=new_cols)
    changes = diff_profiles(old, new)
    attrs = {c["attribute"] for c in changes}
    assert "nullable" in attrs
    assert "unique" in attrs
