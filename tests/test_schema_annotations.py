"""Tests for schema_annotations module."""

import pytest

from schemadrift.schema_annotations import Annotation, AnnotationStore


@pytest.fixture
def store(tmp_path):
    return AnnotationStore(str(tmp_path))


def make_annotation(
    source="orders",
    version="v1",
    column=None,
    note="Initial review.",
    author="alice",
) -> Annotation:
    return Annotation(
        source=source,
        version=version,
        column=column,
        note=note,
        author=author,
    )


def test_add_and_retrieve_snapshot_annotation(store):
    ann = make_annotation()
    store.add(ann)
    results = store.get_for_version("orders", "v1")
    assert len(results) == 1
    assert results[0].note == "Initial review."
    assert results[0].column is None


def test_add_and_retrieve_column_annotation(store):
    ann = make_annotation(column="user_id", note="PII column")
    store.add(ann)
    results = store.get_for_column("orders", "v1", "user_id")
    assert len(results) == 1
    assert results[0].note == "PII column"
    assert results[0].column == "user_id"


def test_get_for_version_filters_correctly(store):
    store.add(make_annotation(version="v1", note="note A"))
    store.add(make_annotation(version="v2", note="note B"))
    v1 = store.get_for_version("orders", "v1")
    v2 = store.get_for_version("orders", "v2")
    assert len(v1) == 1 and v1[0].note == "note A"
    assert len(v2) == 1 and v2[0].note == "note B"


def test_get_for_column_excludes_other_columns(store):
    store.add(make_annotation(column="col_a", note="A"))
    store.add(make_annotation(column="col_b", note="B"))
    results = store.get_for_column("orders", "v1", "col_a")
    assert len(results) == 1
    assert results[0].note == "A"


def test_get_for_missing_version_returns_empty(store):
    results = store.get_for_version("orders", "v99")
    assert results == []


def test_list_sources_empty(store):
    assert store.list_sources() == []


def test_list_sources_after_add(store):
    store.add(make_annotation(source="orders"))
    store.add(make_annotation(source="users"))
    sources = store.list_sources()
    assert set(sources) == {"orders", "users"}


def test_annotation_roundtrip():
    ann = make_annotation(column="price", note="Currency field")
    d = ann.to_dict()
    restored = Annotation.from_dict(d)
    assert restored.source == ann.source
    assert restored.version == ann.version
    assert restored.column == ann.column
    assert restored.note == ann.note
    assert restored.author == ann.author


def test_multiple_annotations_same_version(store):
    store.add(make_annotation(note="first"))
    store.add(make_annotation(note="second"))
    results = store.get_for_version("orders", "v1")
    assert len(results) == 2
    notes = {r.note for r in results}
    assert notes == {"first", "second"}
