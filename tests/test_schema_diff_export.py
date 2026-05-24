"""Tests for schema_diff_export module."""

from __future__ import annotations

import json

import pytest

from schemadrift.schema_diff_export import ExportFormat, export_changelog, export_timeline
from schemadrift.schema_diff_timeline import DriftTimeline, TimelineEntry
from schemadrift.schema_changelog import Changelog, ChangelogEntry


def make_timeline() -> DriftTimeline:
    entries = [
        TimelineEntry(version="v1", has_drift=False, added=0, removed=0, type_changed=0, nullable_changed=0),
        TimelineEntry(version="v2", has_drift=True, added=1, removed=0, type_changed=0, nullable_changed=0),
        TimelineEntry(version="v3", has_drift=True, added=0, removed=1, type_changed=1, nullable_changed=0),
    ]
    return DriftTimeline(source="orders", entries=entries)


def make_changelog() -> Changelog:
    entries = [
        ChangelogEntry(version="v2", change_type="added", column="email", detail=None),
        ChangelogEntry(version="v3", change_type="removed", column="phone", detail=None),
        ChangelogEntry(version="v3", change_type="type_changed", column="age", detail="int -> str"),
    ]
    return Changelog(source="orders", entries=entries)


# --- Timeline JSON ---

def test_timeline_json_returns_list():
    tl = make_timeline()
    result = export_timeline(tl, ExportFormat.JSON)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 3


def test_timeline_json_has_expected_keys():
    tl = make_timeline()
    result = json.loads(export_timeline(tl, ExportFormat.JSON))
    assert "version" in result[0]
    assert "has_drift" in result[0]


# --- Timeline CSV ---

def test_timeline_csv_has_header():
    tl = make_timeline()
    result = export_timeline(tl, ExportFormat.CSV)
    assert result.startswith("version")


def test_timeline_csv_row_count():
    tl = make_timeline()
    lines = export_timeline(tl, ExportFormat.CSV).strip().splitlines()
    assert len(lines) == 4  # header + 3 rows


# --- Timeline Markdown ---

def test_timeline_markdown_contains_header_row():
    tl = make_timeline()
    result = export_timeline(tl, ExportFormat.MARKDOWN)
    assert "| Version |" in result


def test_timeline_markdown_contains_version_values():
    tl = make_timeline()
    result = export_timeline(tl, ExportFormat.MARKDOWN)
    assert "v2" in result
    assert "yes" in result


# --- Changelog JSON ---

def test_changelog_json_returns_list():
    cl = make_changelog()
    result = json.loads(export_changelog(cl, ExportFormat.JSON))
    assert len(result) == 3


def test_changelog_json_has_column_field():
    cl = make_changelog()
    result = json.loads(export_changelog(cl, ExportFormat.JSON))
    assert result[0]["column"] == "email"


# --- Changelog CSV ---

def test_changelog_csv_has_header():
    cl = make_changelog()
    result = export_changelog(cl, ExportFormat.CSV)
    assert "change_type" in result


# --- Changelog Markdown ---

def test_changelog_markdown_contains_detail():
    cl = make_changelog()
    result = export_changelog(cl, ExportFormat.MARKDOWN)
    assert "int -> str" in result


# --- Invalid format ---

def test_invalid_format_raises():
    tl = make_timeline()
    with pytest.raises((ValueError, KeyError)):
        export_timeline(tl, "xml")  # type: ignore
