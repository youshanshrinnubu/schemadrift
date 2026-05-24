"""CLI commands for exporting drift timelines and changelogs."""

from __future__ import annotations

import argparse
import sys

from schemadrift.schema_diff_export import ExportFormat, export_changelog, export_timeline
from schemadrift.schema_diff_timeline import build_timeline
from schemadrift.schema_changelog import build_changelog
from schemadrift.snapshot_store import SnapshotStore


def cmd_export_timeline(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    snapshots = store.load_all(args.source)
    if not snapshots:
        print(f"No snapshots found for source '{args.source}'.")
        sys.exit(1)

    timeline = build_timeline(args.source, snapshots)
    fmt = ExportFormat(args.format)
    output = export_timeline(timeline, fmt)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Timeline exported to {args.output}")
    else:
        print(output)


def cmd_export_changelog(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    snapshots = store.load_all(args.source)
    if not snapshots:
        print(f"No snapshots found for source '{args.source}'.")
        sys.exit(1)

    changelog = build_changelog(args.source, snapshots)
    fmt = ExportFormat(args.format)
    output = export_changelog(changelog, fmt)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Changelog exported to {args.output}")
    else:
        print(output)


def register_diff_export_commands(subparsers: argparse._SubParsersAction) -> None:
    formats = [f.value for f in ExportFormat]

    p_timeline = subparsers.add_parser(
        "export-timeline", help="Export drift timeline for a source"
    )
    p_timeline.add_argument("source", help="Source name")
    p_timeline.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p_timeline.add_argument("--format", choices=formats, default="json", help="Output format")
    p_timeline.add_argument("--output", help="Write output to file instead of stdout")
    p_timeline.set_defaults(func=cmd_export_timeline)

    p_changelog = subparsers.add_parser(
        "export-changelog", help="Export schema changelog for a source"
    )
    p_changelog.add_argument("source", help="Source name")
    p_changelog.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p_changelog.add_argument("--format", choices=formats, default="json", help="Output format")
    p_changelog.add_argument("--output", help="Write output to file instead of stdout")
    p_changelog.set_defaults(func=cmd_export_changelog)
