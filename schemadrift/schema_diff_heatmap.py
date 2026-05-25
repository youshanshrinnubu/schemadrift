from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from schemadrift.drift_detector import DriftReport, ChangeType


@dataclass
class HeatmapCell:
    source: str
    version: str
    change_count: int
    change_types: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "change_count": self.change_count,
            "change_types": self.change_types,
        }


@dataclass
class DriftHeatmap:
    cells: List[HeatmapCell] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"cells": [c.to_dict() for c in self.cells]}

    def sources(self) -> List[str]:
        seen = []
        for cell in self.cells:
            if cell.source not in seen:
                seen.append(cell.source)
        return seen

    def versions(self) -> List[str]:
        seen = []
        for cell in self.cells:
            if cell.version not in seen:
                seen.append(cell.version)
        return seen

    def get_cell(self, source: str, version: str) -> Optional[HeatmapCell]:
        for cell in self.cells:
            if cell.source == source and cell.version == version:
                return cell
        return None

    def hottest_source(self) -> Optional[str]:
        totals: Dict[str, int] = {}
        for cell in self.cells:
            totals[cell.source] = totals.get(cell.source, 0) + cell.change_count
        if not totals:
            return None
        return max(totals, key=lambda s: totals[s])


def build_heatmap(reports: List[DriftReport]) -> DriftHeatmap:
    cells: List[HeatmapCell] = []
    for report in reports:
        change_types = list({c.change_type.value for c in report.changes})
        cells.append(
            HeatmapCell(
                source=report.source,
                version=report.to_version,
                change_count=len(report.changes),
                change_types=change_types,
            )
        )
    return DriftHeatmap(cells=cells)


def format_heatmap_text(heatmap: DriftHeatmap) -> str:
    if not heatmap.cells:
        return "No drift data available for heatmap.\n"
    lines = ["Drift Heatmap", "=" * 40]
    for cell in sorted(heatmap.cells, key=lambda c: (-c.change_count, c.source)):
        types_str = ", ".join(cell.change_types) if cell.change_types else "none"
        lines.append(
            f"  {cell.source} @ {cell.version}: {cell.change_count} change(s) [{types_str}]"
        )
    hottest = heatmap.hottest_source()
    if hottest:
        lines.append(f"\nHottest source: {hottest}")
    return "\n".join(lines) + "\n"
