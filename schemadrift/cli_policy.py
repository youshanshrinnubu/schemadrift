import argparse
import json
import sys
from schemadrift.snapshot_store import SnapshotStore
from schemadrift.schema_policy import load_policy_rules, evaluate_policy


def cmd_policy_check(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    try:
        rules = load_policy_rules(args.policy_file)
    except FileNotFoundError:
        print(f"Policy file not found: {args.policy_file}", file=sys.stderr)
        sys.exit(1)

    if args.version:
        snapshot = store.load_at_version(args.source, args.version)
        if snapshot is None:
            print(f"No snapshot found for {args.source}@{args.version}", file=sys.stderr)
            sys.exit(1)
        snapshots = [snapshot]
    else:
        snapshot = store.load_latest(args.source)
        if snapshot is None:
            print(f"No snapshots found for source: {args.source}", file=sys.stderr)
            sys.exit(1)
        snapshots = [snapshot]

    all_passed = True
    for snap in snapshots:
        result = evaluate_policy(snap, rules)
        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            status = "PASSED" if result.passed else "FAILED"
            print(f"Policy check [{status}] {result.source}@{result.version}")
            for v in result.violations:
                print(f"  [{v.rule_name}] {v.message}")
        if not result.passed:
            all_passed = False

    if not all_passed:
        sys.exit(2)


def cmd_policy_validate_file(args: argparse.Namespace) -> None:
    try:
        rules = load_policy_rules(args.policy_file)
        print(f"Policy file is valid. {len(rules)} rule(s) loaded:")
        for r in rules:
            print(f"  - {r.name}: {r.description}")
    except Exception as e:
        print(f"Invalid policy file: {e}", file=sys.stderr)
        sys.exit(1)


def register_policy_commands(subparsers) -> None:
    p_check = subparsers.add_parser("policy-check", help="Evaluate schema policy rules against a snapshot")
    p_check.add_argument("source", help="Data source name")
    p_check.add_argument("policy_file", help="Path to JSON policy rules file")
    p_check.add_argument("--version", default=None, help="Specific version to check")
    p_check.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p_check.add_argument("--format", choices=["text", "json"], default="text")
    p_check.set_defaults(func=cmd_policy_check)

    p_validate = subparsers.add_parser("policy-validate", help="Validate a policy rules file")
    p_validate.add_argument("policy_file", help="Path to JSON policy rules file")
    p_validate.set_defaults(func=cmd_policy_validate_file)
