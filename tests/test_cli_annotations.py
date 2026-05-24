"""Tests for CLI annotation commands."""

import argparse
import pytest

from schemadrift.schema_annotations import AnnotationStore
from schemadrift.cli_annotations import (
    cmd_annotation_add,
    cmd_annotation_list,
    cmd_annotation_sources,
)


@pytest.fixture
def store_dir(tmp_path):
    return str(tmp_path)


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "store_dir": "/tmp",
        "source": "orders",
        "version": "v1",
        "note": "Test note",
        "author": "tester",
        "column": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_annotation_add_creates_entry(store_dir, capsys):
    args = make_args(store_dir=store_dir)
    cmd_annotation_add(args)
    store = AnnotationStore(store_dir)
    results = store.get_for_version("orders", "v1")
    assert len(results) == 1
    assert results[0].note == "Test note"
    assert results[0].author == "tester"


def test_cmd_annotation_add_with_column(store_dir, capsys):
    args = make_args(store_dir=store_dir, column="price")
    cmd_annotation_add(args)
    store = AnnotationStore(store_dir)
    results = store.get_for_column("orders", "v1", "price")
    assert len(results) == 1
    captured = capsys.readouterr()
    assert "price" in captured.out


def test_cmd_annotation_list_shows_notes(store_dir, capsys):
    store = AnnotationStore(store_dir)
    from schemadrift.schema_annotations import Annotation
    store.add(Annotation("orders", "v1", None, "hello world", "bob"))
    args = make_args(store_dir=store_dir)
    cmd_annotation_list(args)
    captured = capsys.readouterr()
    assert "hello world" in captured.out
    assert "bob" in captured.out


def test_cmd_annotation_list_empty(store_dir, capsys):
    args = make_args(store_dir=store_dir)
    cmd_annotation_list(args)
    captured = capsys.readouterr()
    assert "No annotations" in captured.out


def test_cmd_annotation_sources_empty(store_dir, capsys):
    args = make_args(store_dir=store_dir)
    cmd_annotation_sources(args)
    captured = capsys.readouterr()
    assert "No annotated sources" in captured.out


def test_cmd_annotation_sources_lists_names(store_dir, capsys):
    from schemadrift.schema_annotations import Annotation
    store = AnnotationStore(store_dir)
    store.add(Annotation("orders", "v1", None, "note", "alice"))
    store.add(Annotation("users", "v1", None, "note", "alice"))
    args = make_args(store_dir=store_dir)
    cmd_annotation_sources(args)
    captured = capsys.readouterr()
    assert "orders" in captured.out
    assert "users" in captured.out
