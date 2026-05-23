"""CLI sub-commands for baseline management.

Intended to be registered on the top-level parser built in cli.py.
"""

from __future__ import annotations

import argparse
import sys

from schemadrift.baseline import BaselineStore
from schemadrift.baseline_diff import diff_against_baseline, promote_to_baseline
from schemadrift.drift_formatter import OutputFormat, format_report
from schemadrift.snapshot_store import SnapshotStore


def cmd_baseline_set(args: argparse.Namespace) -> int:
    """Pin the latest (or specified) snapshot as a named baseline."""
    snap_store = SnapshotStore(args.store_dir)
    bl_store = BaselineStore(args.store_dir)

    if args.version:
        snapshot = snap_store.load_at_version(args.source, args.version)
    else:
        snapshot = snap_store.load_latest(args.source)

    if snapshot is None:
        print(f"No snapshot found for source '{args.source}'.", file=sys.stderr)
        return 1

    bl = promote_to_baseline(snapshot, args.name, store=bl_store)
    print(f"Baseline '{bl.name}' set to version {snapshot.version} of '{args.source}'.")
    return 0


def cmd_baseline_diff(args: argparse.Namespace) -> int:
    """Diff the latest snapshot of a source against a named baseline."""
    snap_store = SnapshotStore(args.store_dir)
    bl_store = BaselineStore(args.store_dir)

    snapshot = snap_store.load_latest(args.source)
    if snapshot is None:
        print(f"No snapshot found for source '{args.source}'.", file=sys.stderr)
        return 1

    try:
        result = diff_against_baseline(snapshot, args.name, store=bl_store)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    fmt = OutputFormat(args.format)
    print(format_report(result.report, fmt))
    return 1 if result.has_drift else 0


def cmd_baseline_list(args: argparse.Namespace) -> int:
    """List all stored baselines."""
    bl_store = BaselineStore(args.store_dir)
    names = bl_store.list_names()
    if not names:
        print("No baselines stored.")
        return 0
    for name in names:
        bl = bl_store.load(name)
        print(f"  {name}  ({bl.source}, version {bl.snapshot.version})")
    return 0


def cmd_baseline_delete(args: argparse.Namespace) -> int:
    """Remove a named baseline."""
    bl_store = BaselineStore(args.store_dir)
    if bl_store.delete(args.name):
        print(f"Baseline '{args.name}' deleted.")
        return 0
    print(f"Baseline '{args.name}' not found.", file=sys.stderr)
    return 1


def register_baseline_commands(subparsers: argparse._SubParsersAction, store_dir: str) -> None:
    """Attach baseline sub-commands to an existing ArgumentParser subparsers group."""
    p = subparsers.add_parser("baseline", help="Manage named schema baselines")
    bs = p.add_subparsers(dest="baseline_cmd", required=True)

    # baseline set
    p_set = bs.add_parser("set", help="Pin a snapshot as a named baseline")
    p_set.add_argument("name", help="Baseline name")
    p_set.add_argument("source", help="Data source identifier")
    p_set.add_argument("--version", type=int, default=None)
    p_set.add_argument("--store-dir", default=store_dir)
    p_set.set_defaults(func=cmd_baseline_set)

    # baseline diff
    p_diff = bs.add_parser("diff", help="Diff latest snapshot against a baseline")
    p_diff.add_argument("name", help="Baseline name")
    p_diff.add_argument("source", help="Data source identifier")
    p_diff.add_argument("--format", choices=["text", "markdown"], default="text")
    p_diff.add_argument("--store-dir", default=store_dir)
    p_diff.set_defaults(func=cmd_baseline_diff)

    # baseline list
    p_list = bs.add_parser("list", help="List all baselines")
    p_list.add_argument("--store-dir", default=store_dir)
    p_list.set_defaults(func=cmd_baseline_list)

    # baseline delete
    p_del = bs.add_parser("delete", help="Remove a baseline")
    p_del.add_argument("name", help="Baseline name")
    p_del.add_argument("--store-dir", default=store_dir)
    p_del.set_defaults(func=cmd_baseline_delete)
