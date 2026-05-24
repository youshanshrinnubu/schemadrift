"""CLI commands for column profile management."""

from __future__ import annotations
import argparse
import json
import sys
from typing import List

from schemadrift.column_profile import ColumnProfile, SchemaProfile, diff_profiles
from schemadrift.profile_store import ProfileStore


def cmd_profile_save(args: argparse.Namespace) -> None:
    """Save a profile from a JSON file."""
    try:
        data = json.loads(args.json)
        profile = SchemaProfile.from_dict(data)
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"Error parsing profile JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    store = ProfileStore(args.store_dir)
    store.save(profile)
    print(f"Saved profile for '{profile.source}' at version '{profile.version}'.")


def cmd_profile_diff(args: argparse.Namespace) -> None:
    """Diff two saved profile versions."""
    store = ProfileStore(args.store_dir)
    old = store.load(args.source, args.old_version)
    new = store.load(args.source, args.new_version)

    if old is None:
        print(f"Profile not found: {args.source}@{args.old_version}", file=sys.stderr)
        sys.exit(1)
    if new is None:
        print(f"Profile not found: {args.source}@{args.new_version}", file=sys.stderr)
        sys.exit(1)

    changes = diff_profiles(old, new)
    if not changes:
        print("No profile attribute changes detected.")
        return

    print(f"Profile changes ({args.source}: {args.old_version} -> {args.new_version})")
    for ch in changes:
        print(f"  [{ch['column']}] {ch['attribute']}: {ch['before']!r} -> {ch['after']!r}")


def cmd_profile_list(args: argparse.Namespace) -> None:
    """List saved versions for a source."""
    store = ProfileStore(args.store_dir)
    versions = store.list_versions(args.source)
    if not versions:
        print(f"No profiles stored for '{args.source}'.")
        return
    for v in versions:
        print(v)


def cmd_profile_show(args: argparse.Namespace) -> None:
    """Print the stored profile for a given source and version as JSON."""
    store = ProfileStore(args.store_dir)
    profile = store.load(args.source, args.version)
    if profile is None:
        print(f"Profile not found: {args.source}@{args.version}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(profile.to_dict(), indent=2))


def register_profile_commands(subparsers: argparse._SubParsersAction, store_dir: str) -> None:
    p_save = subparsers.add_parser("profile-save", help="Save a column profile")
    p_save.add_argument("json", help="JSON string of the SchemaProfile")
    p_save.set_defaults(func=cmd_profile_save, store_dir=store_dir)

    p_diff = subparsers.add_parser("profile-diff", help="Diff two profile versions")
    p_diff.add_argument("source", help="Data source name")
    p_diff.add_argument("old_version", help="Older version")
    p_diff.add_argument("new_version", help="Newer version")
    p_diff.set_defaults(func=cmd_profile_diff, store_dir=store_dir)

    p_list = subparsers.add_parser("profile-list", help="List profile versions for a source")
    p_list.add_argument("source", help="Data source name")
    p_list.set_defaults(func=cmd_profile_list, store_dir=store_dir)

    p_show = subparsers.add_parser("profile-show", help="Show a stored profile as JSON")
    p_show.add_argument("source", help="Data source name")
    p_show.add_argument("version", help="Profile version to display")
    p_show.set_defaults(func=cmd_profile_show, store_dir=store_dir)
