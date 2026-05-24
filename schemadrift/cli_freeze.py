"""CLI commands for schema freeze management."""

import argparse
import os

from schemadrift.schema_freeze import FreezeStore


def cmd_freeze_set(args: argparse.Namespace) -> None:
    store = FreezeStore(os.path.join(args.store_dir, "freezes"))
    entry = store.freeze(
        source=args.source,
        version=args.version,
        frozen_by=args.by,
        reason=args.reason or "",
    )
    print(f"Frozen: {entry.source}@{entry.version} by {entry.frozen_by}")
    if entry.reason:
        print(f"Reason: {entry.reason}")


def cmd_freeze_remove(args: argparse.Namespace) -> None:
    store = FreezeStore(os.path.join(args.store_dir, "freezes"))
    removed = store.unfreeze(source=args.source, version=args.version)
    if removed:
        print(f"Unfrozen: {args.source}@{args.version}")
    else:
        print(f"No freeze found for {args.source}@{args.version}")


def cmd_freeze_check(args: argparse.Namespace) -> None:
    store = FreezeStore(os.path.join(args.store_dir, "freezes"))
    frozen = store.is_frozen(source=args.source, version=args.version)
    status = "FROZEN" if frozen else "not frozen"
    print(f"{args.source}@{args.version}: {status}")


def cmd_freeze_list(args: argparse.Namespace) -> None:
    store = FreezeStore(os.path.join(args.store_dir, "freezes"))
    entries = store.list_frozen(args.source)
    if not entries:
        print(f"No frozen versions for source: {args.source}")
        return
    print(f"Frozen versions for {args.source}:")
    for e in entries:
        reason_str = f" — {e.reason}" if e.reason else ""
        print(f"  {e.version}  (by {e.frozen_by} at {e.frozen_at}){reason_str}")


def register_freeze_commands(subparsers: argparse._SubParsersAction, store_dir: str) -> None:
    freeze_parser = subparsers.add_parser("freeze", help="Manage schema freezes")
    freeze_sub = freeze_parser.add_subparsers(dest="freeze_cmd")

    p_set = freeze_sub.add_parser("set", help="Freeze a schema version")
    p_set.add_argument("source")
    p_set.add_argument("version")
    p_set.add_argument("--by", required=True, help="Who is freezing")
    p_set.add_argument("--reason", default="", help="Reason for freeze")
    p_set.add_argument("--store-dir", default=store_dir)
    p_set.set_defaults(func=cmd_freeze_set)

    p_remove = freeze_sub.add_parser("remove", help="Unfreeze a schema version")
    p_remove.add_argument("source")
    p_remove.add_argument("version")
    p_remove.add_argument("--store-dir", default=store_dir)
    p_remove.set_defaults(func=cmd_freeze_remove)

    p_check = freeze_sub.add_parser("check", help="Check if a version is frozen")
    p_check.add_argument("source")
    p_check.add_argument("version")
    p_check.add_argument("--store-dir", default=store_dir)
    p_check.set_defaults(func=cmd_freeze_check)

    p_list = freeze_sub.add_parser("list", help="List frozen versions for a source")
    p_list.add_argument("source")
    p_list.add_argument("--store-dir", default=store_dir)
    p_list.set_defaults(func=cmd_freeze_list)
