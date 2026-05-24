"""CLI commands for schema validation."""

import argparse
import json
import sys

from schemadrift.snapshot_store import SnapshotStore
from schemadrift.schema_validator import validate_snapshot, BUILTIN_RULES, ViolationLevel


def cmd_validate(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    snapshot = store.load_latest(args.source)

    if snapshot is None:
        print(f"No snapshots found for source '{args.source}'.")
        sys.exit(1)

    report = validate_snapshot(snapshot)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
        if report.has_errors:
            sys.exit(2)
        return

    # Default: text output
    print(f"Validation report for '{report.source}' @ {report.version}")
    if not report.violations:
        print("  ✓ No violations found.")
    else:
        for v in report.violations:
            prefix = "[ERROR]" if v.level == ViolationLevel.ERROR else "[WARN] "
            col_info = f" (column: {v.column})" if v.column else ""
            print(f"  {prefix} {v.message}{col_info}")

    if report.has_errors:
        sys.exit(2)


def cmd_validate_list_rules(args: argparse.Namespace) -> None:
    print("Built-in validation rules:")
    for rule in BUILTIN_RULES:
        print(f"  [{rule.level.value.upper()}] {rule.name}: {rule.description}")


def register_validator_commands(subparsers: argparse._SubParsersAction) -> None:
    validate_parser = subparsers.add_parser("validate", help="Validate the latest snapshot for a source.")
    validate_parser.add_argument("source", help="Data source name.")
    validate_parser.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory.")
    validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    validate_parser.set_defaults(func=cmd_validate)

    rules_parser = subparsers.add_parser("validate-rules", help="List available validation rules.")
    rules_parser.set_defaults(func=cmd_validate_list_rules)
