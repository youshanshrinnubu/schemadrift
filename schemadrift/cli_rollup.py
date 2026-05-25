"""CLI commands for drift rollup reporting."""

import argparse
import json
from typing import List

from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import compare_snapshots
from schemadrift.schema_diff_rollup import rollup_reports, DriftRollup


def cmd_rollup(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    sources = args.sources if args.sources else store.list_sources()

    all_reports = []
    for source in sources:
        snapshots = store.load_all(source)
        for i in range(1, len(snapshots)):
            report = compare_snapshots(snapshots[i - 1], snapshots[i])
            all_reports.append(report)

    rollup = rollup_reports(
        all_reports,
        window_start=args.window_start or None,
        window_end=args.window_end or None,
    )

    if args.format == "json":
        print(json.dumps(rollup.to_dict(), indent=2))
    else:
        _print_text_rollup(rollup)


def _print_text_rollup(rollup: DriftRollup) -> None:
    print(f"Drift Rollup")
    if rollup.window_start or rollup.window_end:
        print(f"  Window: {rollup.window_start or '?'} -> {rollup.window_end or '?'}")
    print(f"  Sources with drift: {rollup.total_sources_with_drift}/{len(rollup.sources)}")
    print()
    for source, entry in sorted(rollup.sources.items()):
        drift_flag = "*" if entry.reports_with_drift > 0 else " "
        print(f"  [{drift_flag}] {source}")
        print(f"       Reports: {entry.total_reports}  |  With drift: {entry.reports_with_drift}")
        if entry.change_type_counts:
            counts = ", ".join(f"{k}={v}" for k, v in sorted(entry.change_type_counts.items()))
            print(f"       Changes: {counts}")


def register_rollup_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("rollup", help="Show aggregated drift rollup across sources")
    p.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p.add_argument("--sources", nargs="*", help="Limit to specific sources")
    p.add_argument("--window-start", default="", help="Optional window start timestamp")
    p.add_argument("--window-end", default="", help="Optional window end timestamp")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_rollup)
