"""CLI commands for schema drift blame."""

import argparse
import json
from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import compare_snapshots
from schemadrift.schema_diff_blame import build_blame


def cmd_blame(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    snapshots = store.load_all(args.source)
    if len(snapshots) < 2:
        print(f"Not enough snapshots for source '{args.source}' to compute blame.")
        return

    target_version = args.version
    matching = [s for s in snapshots if s.version == target_version]
    if not matching:
        print(f"Version '{target_version}' not found for source '{args.source}'.")
        return

    idx = snapshots.index(matching[0])
    if idx == 0:
        print(f"Version '{target_version}' is the first snapshot; no previous version to compare.")
        return

    prev = snapshots[idx - 1]
    curr = matching[0]
    report = compare_snapshots(prev, curr)

    notes = {}
    tags = {}
    if args.notes:
        try:
            notes = json.loads(args.notes)
        except json.JSONDecodeError:
            print("Warning: --notes is not valid JSON, ignoring.")

    summary = build_blame(report, notes=notes, tags=tags)

    if not summary.has_blame:
        print(f"No drift detected for {args.source} at version {target_version}.")
        return

    print(f"Blame for {args.source} @ {target_version}:")
    for entry in summary.entries:
        note_str = f" | note: {entry.note}" if entry.note else ""
        print(f"  [{entry.change_type}] {entry.column}{note_str}")


def register_blame_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("blame", help="Show blame for drift changes at a given version")
    p.add_argument("source", help="Data source name")
    p.add_argument("version", help="Version to inspect")
    p.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p.add_argument("--notes", default=None, help="JSON mapping of column name to note string")
    p.set_defaults(func=cmd_blame)
