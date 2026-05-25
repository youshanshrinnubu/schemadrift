from __future__ import annotations
import argparse
from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import compare_snapshots
from schemadrift.history_analyzer import compare_consecutive
from schemadrift.schema_diff_heatmap import build_heatmap, format_heatmap_text


def cmd_heatmap(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    sources = store.list_sources()
    if not sources:
        print("No sources found.")
        return

    all_reports = []
    for source in sources:
        snapshots = store.load_all(source)
        reports = compare_consecutive(snapshots)
        all_reports.extend(reports)

    if not all_reports:
        print("No drift reports generated — no consecutive snapshot pairs found.")
        return

    heatmap = build_heatmap(all_reports)

    if getattr(args, "format", "text") == "json":
        import json
        print(json.dumps(heatmap.to_dict(), indent=2))
    else:
        print(format_heatmap_text(heatmap))


def register_heatmap_commands(
    subparsers: argparse._SubParsersAction,
    store_dir_default: str = ".schemadrift",
) -> None:
    p = subparsers.add_parser(
        "heatmap",
        help="Show a drift heatmap across all sources and versions",
    )
    p.add_argument(
        "--store-dir",
        default=store_dir_default,
        help="Path to snapshot store directory",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_heatmap)
