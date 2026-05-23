"""Tracks and compares basic column-level statistics across schema snapshots."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class ColumnStat:
    column_name: str
    data_type: str
    appears_in_versions: List[str] = field(default_factory=list)
    type_changes: int = 0

    def to_dict(self) -> dict:
        return {
            "column_name": self.column_name,
            "data_type": self.data_type,
            "appears_in_versions": self.appears_in_versions,
            "type_changes": self.type_changes,
        }


@dataclass
class ColumnStatsReport:
    source: str
    total_versions_analyzed: int
    stats: Dict[str, ColumnStat] = field(default_factory=dict)

    def most_changed_columns(self, top_n: int = 5) -> List[ColumnStat]:
        """Return columns sorted by number of type changes, descending."""
        sorted_stats = sorted(
            self.stats.values(), key=lambda s: s.type_changes, reverse=True
        )
        return sorted_stats[:top_n]

    def columns_present_in_all_versions(self) -> List[str]:
        """Return column names that appear in every analyzed version."""
        return [
            name
            for name, stat in self.stats.items()
            if len(stat.appears_in_versions) == self.total_versions_analyzed
        ]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "total_versions_analyzed": self.total_versions_analyzed,
            "stats": {name: stat.to_dict() for name, stat in self.stats.items()},
        }


def compute_column_stats(snapshots: List[SchemaSnapshot]) -> Optional[ColumnStatsReport]:
    """Compute column-level statistics across a list of snapshots for the same source."""
    if not snapshots:
        return None

    source = snapshots[0].source
    report = ColumnStatsReport(source=source, total_versions_analyzed=len(snapshots))

    prev_types: Dict[str, str] = {}

    for snapshot in snapshots:
        current_types: Dict[str, str] = {
            col.name: col.data_type for col in snapshot.columns
        }

        for col_name, data_type in current_types.items():
            if col_name not in report.stats:
                report.stats[col_name] = ColumnStat(
                    column_name=col_name, data_type=data_type
                )
            stat = report.stats[col_name]
            stat.appears_in_versions.append(snapshot.version)
            stat.data_type = data_type

            if col_name in prev_types and prev_types[col_name] != data_type:
                stat.type_changes += 1

        prev_types = current_types

    return report
