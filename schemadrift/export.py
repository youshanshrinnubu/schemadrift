"""Export drift reports and snapshots to files in various formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from schemadrift.drift_detector import DriftReport
from schemadrift.drift_formatter import OutputFormat, format_report
from schemadrift.schema_snapshot import SchemaSnapshot


def export_report(
    report: DriftReport,
    output_path: Path,
    fmt: OutputFormat = OutputFormat.TEXT,
) -> Path:
    """Write a formatted drift report to *output_path*.

    The file extension of *output_path* is used as a hint when *fmt* is not
    explicitly overridden by the caller, but the caller-supplied *fmt* always
    wins.

    Returns the resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_report(report, fmt)
    output_path.write_text(content, encoding="utf-8")
    return output_path.resolve()


def export_snapshot(
    snapshot: SchemaSnapshot,
    output_path: Path,
) -> Path:
    """Serialise a SchemaSnapshot to a JSON file at *output_path*.

    Returns the resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = snapshot.to_dict()
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path.resolve()


def infer_format(path: Path) -> Optional[OutputFormat]:
    """Guess an OutputFormat from a file extension, or return None."""
    suffix = Path(path).suffix.lower()
    mapping = {
        ".txt": OutputFormat.TEXT,
        ".md": OutputFormat.MARKDOWN,
        ".json": OutputFormat.JSON,
    }
    return mapping.get(suffix)
