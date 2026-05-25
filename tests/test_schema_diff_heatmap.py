import pytest
from schemadrift.drift_detector import DriftReport, DriftChange, ChangeType
from schemadrift.schema_diff_heatmap import (
    build_heatmap,
    format_heatmap_text,
    HeatmapCell,
    DriftHeatmap,
)


def make_change(col: str, change_type: ChangeType) -> DriftChange:
    return DriftChange(
        column=col,
        change_type=change_type,
        before=None,
        after=None,
    )


def make_report(
    source: str, to_version: str, changes: list
) -> DriftReport:
    return DriftReport(
        source=source,
        from_version="v1",
        to_version=to_version,
        changes=changes,
    )


def test_empty_reports_returns_empty_heatmap():
    heatmap = build_heatmap([])
    assert heatmap.cells == []
    assert heatmap.sources() == []
    assert heatmap.versions() == []


def test_single_report_no_changes():
    report = make_report("db.users", "v2", [])
    heatmap = build_heatmap([report])
    assert len(heatmap.cells) == 1
    cell = heatmap.cells[0]
    assert cell.source == "db.users"
    assert cell.version == "v2"
    assert cell.change_count == 0
    assert cell.change_types == []


def test_single_report_with_changes():
    changes = [
        make_change("email", ChangeType.ADDED),
        make_change("phone", ChangeType.ADDED),
    ]
    report = make_report("db.users", "v2", changes)
    heatmap = build_heatmap([report])
    cell = heatmap.cells[0]
    assert cell.change_count == 2
    assert ChangeType.ADDED.value in cell.change_types


def test_multiple_reports_multiple_sources():
    r1 = make_report("src.a", "v2", [make_change("col1", ChangeType.ADDED)])
    r2 = make_report("src.b", "v2", [
        make_change("col1", ChangeType.REMOVED),
        make_change("col2", ChangeType.REMOVED),
    ])
    heatmap = build_heatmap([r1, r2])
    assert len(heatmap.cells) == 2
    assert set(heatmap.sources()) == {"src.a", "src.b"}


def test_hottest_source_returns_most_changed():
    r1 = make_report("src.a", "v2", [make_change("x", ChangeType.ADDED)])
    r2 = make_report("src.b", "v2", [
        make_change("x", ChangeType.REMOVED),
        make_change("y", ChangeType.REMOVED),
        make_change("z", ChangeType.TYPE_CHANGED),
    ])
    heatmap = build_heatmap([r1, r2])
    assert heatmap.hottest_source() == "src.b"


def test_hottest_source_returns_none_when_empty():
    heatmap = DriftHeatmap(cells=[])
    assert heatmap.hottest_source() is None


def test_get_cell_returns_correct_cell():
    r1 = make_report("src.a", "v3", [make_change("col", ChangeType.ADDED)])
    heatmap = build_heatmap([r1])
    cell = heatmap.get_cell("src.a", "v3")
    assert cell is not None
    assert cell.change_count == 1


def test_get_cell_returns_none_for_missing():
    heatmap = DriftHeatmap(cells=[])
    assert heatmap.get_cell("missing", "v1") is None


def test_format_heatmap_text_no_data():
    heatmap = DriftHeatmap(cells=[])
    output = format_heatmap_text(heatmap)
    assert "No drift data" in output


def test_format_heatmap_text_with_cells():
    changes = [make_change("col", ChangeType.ADDED)]
    heatmap = build_heatmap([make_report("src.x", "v2", changes)])
    output = format_heatmap_text(heatmap)
    assert "src.x" in output
    assert "v2" in output
    assert "1 change" in output


def test_to_dict_structure():
    changes = [make_change("col", ChangeType.TYPE_CHANGED)]
    heatmap = build_heatmap([make_report("src.z", "v5", changes)])
    d = heatmap.to_dict()
    assert "cells" in d
    assert d["cells"][0]["source"] == "src.z"
    assert d["cells"][0]["change_count"] == 1
