"""Command-line interface for schemadrift — capture and compare schema snapshots."""

import argparse
import json
import sys
from datetime import datetime

from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import DriftReport


def cmd_capture(args, store: SnapshotStore) -> int:
    """Read a JSON snapshot file and persist it to the store."""
    try:
        with open(args.file, "r") as f:
            data = json.load(f)
        snapshot = SchemaSnapshot.from_dict(data)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Error reading snapshot file: {e}", file=sys.stderr)
        return 1
    store.save(snapshot)
    print(f"Captured snapshot for '{snapshot.source_name}' version '{snapshot.version}'.")
    return 0


def cmd_diff(args, store: SnapshotStore) -> int:
    """Compare two versions of a source and print a drift report."""
    old = store.load_at_version(args.source, args.from_version)
    new = store.load_at_version(args.source, args.to_version)

    if old is None:
        print(f"Version '{args.from_version}' not found for source '{args.source}'.", file=sys.stderr)
        return 1
    if new is None:
        print(f"Version '{args.to_version}' not found for source '{args.source}'.", file=sys.stderr)
        return 1

    report = DriftReport.compare(old, new)
    if not report.has_drift():
        print("No schema drift detected.")
        return 0

    print(f"Schema drift detected ({len(report.changes)} change(s)):")
    for change in report.changes:
        print(f"  [{change.change_type.value}] column='{change.column_name}' "
              f"from={change.old_value!r} to={change.new_value!r}")
    return 0


def cmd_list(args, store: SnapshotStore) -> int:
    """List all snapshots for a source."""
    snapshots = store.load_all(args.source)
    if not snapshots:
        print(f"No snapshots found for '{args.source}'.")
        return 0
    print(f"Snapshots for '{args.source}':")
    for s in snapshots:
        print(f"  version={s.version}  captured_at={s.captured_at}  columns={len(s.columns)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="schemadrift", description="Schema drift detector")
    parser.add_argument("--store-dir", default=".schemadrift", help="Directory for snapshot storage")
    sub = parser.add_subparsers(dest="command", required=True)

    capture_p = sub.add_parser("capture", help="Capture a schema snapshot from a JSON file")
    capture_p.add_argument("file", help="Path to snapshot JSON file")

    diff_p = sub.add_parser("diff", help="Compare two schema versions")
    diff_p.add_argument("source", help="Source name")
    diff_p.add_argument("from_version", help="Baseline version")
    diff_p.add_argument("to_version", help="New version")

    list_p = sub.add_parser("list", help="List snapshots for a source")
    list_p.add_argument("source", help="Source name")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = SnapshotStore(store_dir=args.store_dir)
    dispatch = {"capture": cmd_capture, "diff": cmd_diff, "list": cmd_list}
    return dispatch[args.command](args, store)


if __name__ == "__main__":
    sys.exit(main())
