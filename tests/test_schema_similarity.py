"""Tests for schemadrift.schema_similarity."""

import pytest
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_similarity import (
    compute_similarity,
    most_similar_version,
    SimilarityResult,
)


def make_snapshot(version: str, columns: list[tuple[str, str]]) -> SchemaSnapshot:
    return SchemaSnapshot(
        source="db.users",
        version=version,
        columns=[ColumnSchema(name=n, data_type=t) for n, t in columns],
    )


def test_identical_schemas_score_one():
    cols = [("id", "int"), ("name", "str"), ("email", "str")]
    snap_a = make_snapshot("v1", cols)
    snap_b = make_snapshot("v2", cols)
    result = compute_similarity(snap_a, snap_b)
    assert result.column_overlap_score == 1.0
    assert result.type_match_score == 1.0
    assert result.overall_score == 1.0


def test_completely_different_schemas_score_zero():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("email", "str")])
    result = compute_similarity(snap_a, snap_b)
    assert result.column_overlap_score == 0.0
    # no shared columns, so type_match defaults to 1.0
    assert result.type_match_score == 1.0
    assert result.overall_score == pytest.approx(0.4, rel=1e-3)


def test_partial_column_overlap():
    snap_a = make_snapshot("v1", [("id", "int"), ("name", "str")])
    snap_b = make_snapshot("v2", [("id", "int"), ("email", "str")])
    result = compute_similarity(snap_a, snap_b)
    # union=3, intersection=1 => overlap=1/3
    assert result.column_overlap_score == pytest.approx(1 / 3, rel=1e-3)
    assert result.type_match_score == 1.0  # shared 'id' has same type


def test_type_mismatch_reduces_type_score():
    snap_a = make_snapshot("v1", [("id", "int"), ("score", "float")])
    snap_b = make_snapshot("v2", [("id", "int"), ("score", "int")])
    result = compute_similarity(snap_a, snap_b)
    assert result.column_overlap_score == 1.0
    assert result.type_match_score == pytest.approx(0.5, rel=1e-3)


def test_empty_schemas_score_one():
    snap_a = make_snapshot("v1", [])
    snap_b = make_snapshot("v2", [])
    result = compute_similarity(snap_a, snap_b)
    assert result.overall_score == 1.0


def test_to_dict_contains_expected_keys():
    snap_a = make_snapshot("v1", [("id", "int")])
    snap_b = make_snapshot("v2", [("id", "int")])
    d = compute_similarity(snap_a, snap_b).to_dict()
    assert set(d.keys()) == {
        "source", "version_a", "version_b",
        "column_overlap_score", "type_match_score", "overall_score",
    }


def test_most_similar_version_returns_closest():
    target = make_snapshot("v3", [("id", "int"), ("name", "str"), ("age", "int")])
    close = make_snapshot("v2", [("id", "int"), ("name", "str"), ("age", "int")])
    far = make_snapshot("v1", [("x", "float"), ("y", "float")])
    result = most_similar_version(target, [far, close])
    assert result is close


def test_most_similar_version_empty_candidates_returns_none():
    target = make_snapshot("v1", [("id", "int")])
    assert most_similar_version(target, []) is None
