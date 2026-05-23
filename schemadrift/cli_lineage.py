"""CLI commands for column lineage / rename detection."""

import argparse
import json

from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import compare_snapshots
from schemadrift.column_lineage import detect_lineage_hints


def cmd_lineage_hints(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    snapshots = store.load_all(args.source)

    if len(snapshots) < 2:
        print(f"Not enough snapshots for source '{args.source}' to detect lineage.")
        return

    snapshots.sort(key=lambda s: s.version)

    all_hints = []
    for i in range(len(snapshots) - 1):
        old_snap = snapshots[i]
        new_snap = snapshots[i + 1]
        report = compare_snapshots(old_snap, new_snap)
        hints = detect_lineage_hints(report, min_confidence=args.min_confidence)
        all_hints.extend(hints)

    if not all_hints:
        print("No rename hints detected.")
        return

    if args.output_format == "json":
        print(json.dumps([h.to_dict() for h in all_hints], indent=2))
    else:
        print(f"Column lineage hints for source: {args.source}")
        print("-" * 50)
        for h in all_hints:
            print(
                f"  [{h.version_from} -> {h.version_to}] "
                f"'{h.old_name}' may have been renamed to '{h.new_name}' "
                f"(confidence: {h.confidence:.0%})"
            )


def register_lineage_commands(subparsers: argparse._SubParsersAction) -> None:
    lineage_parser = subparsers.add_parser(
        "lineage", help="Detect likely column renames across snapshot history"
    )
    lineage_sub = lineage_parser.add_subparsers(dest="lineage_cmd")

    hints_parser = lineage_sub.add_parser(
        "hints", help="Show rename hints for a source"
    )
    hints_parser.add_argument("source", help="Data source name")
    hints_parser.add_argument(
        "--store-dir", default=".schemadrift", help="Snapshot store directory"
    )
    hints_parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence score (0.0-1.0) to report a hint",
    )
    hints_parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    hints_parser.set_defaults(func=cmd_lineage_hints)
