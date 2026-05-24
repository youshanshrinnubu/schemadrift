"""CLI commands for managing the schema watchlist."""

from __future__ import annotations

import argparse

from schemadrift.schema_watchlist import WatchlistStore


def cmd_watch_add(args: argparse.Namespace) -> None:
    store = WatchlistStore(args.store_dir)
    wl = store.load()
    wl.add(source=args.source, column=args.column, reason=args.reason or "")
    store.save(wl)
    col_info = f" (column: {args.column})" if args.column else ""
    print(f"Watching: {args.source}{col_info}")


def cmd_watch_remove(args: argparse.Namespace) -> None:
    store = WatchlistStore(args.store_dir)
    wl = store.load()
    removed = wl.remove(source=args.source, column=args.column)
    if removed:
        store.save(wl)
        print(f"Removed watch for: {args.source}")
    else:
        print(f"No matching watch entry found for: {args.source}")


def cmd_watch_list(args: argparse.Namespace) -> None:
    store = WatchlistStore(args.store_dir)
    wl = store.load()
    if not wl.entries:
        print("No watched sources or columns.")
        return
    print(f"{'SOURCE':<24} {'COLUMN':<24} REASON")
    print("-" * 64)
    for entry in sorted(wl.entries, key=lambda e: (e.source, e.column or "")):
        col = entry.column or "(all columns)"
        print(f"{entry.source:<24} {col:<24} {entry.reason}")


def cmd_watch_check(args: argparse.Namespace) -> None:
    """Check whether a source (and optional column) is currently watched."""
    store = WatchlistStore(args.store_dir)
    wl = store.load()
    watched = wl.is_watched(args.source, column=args.column)
    status = "WATCHED" if watched else "not watched"
    col_info = f" column={args.column}" if args.column else ""
    print(f"{args.source}{col_info}: {status}")


def register_watchlist_commands(subparsers: argparse._SubParsersAction, store_dir: str) -> None:
    watch_parser = subparsers.add_parser("watch", help="Manage schema watchlist")
    watch_sub = watch_parser.add_subparsers(dest="watch_cmd", required=True)

    p_add = watch_sub.add_parser("add", help="Add a source or column to the watchlist")
    p_add.add_argument("source")
    p_add.add_argument("--column", default=None)
    p_add.add_argument("--reason", default="")
    p_add.set_defaults(func=cmd_watch_add, store_dir=store_dir)

    p_rm = watch_sub.add_parser("remove", help="Remove a watch entry")
    p_rm.add_argument("source")
    p_rm.add_argument("--column", default=None)
    p_rm.set_defaults(func=cmd_watch_remove, store_dir=store_dir)

    p_list = watch_sub.add_parser("list", help="List all watch entries")
    p_list.set_defaults(func=cmd_watch_list, store_dir=store_dir)

    p_check = watch_sub.add_parser("check", help="Check if a source/column is watched")
    p_check.add_argument("source")
    p_check.add_argument("--column", default=None)
    p_check.set_defaults(func=cmd_watch_check, store_dir=store_dir)
