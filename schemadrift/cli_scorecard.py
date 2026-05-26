import argparse
import json
from typing import Dict, List

from schemadrift.snapshot_store import SnapshotStore
from schemadrift.drift_detector import compare_snapshots
from schemadrift.schema_diff_scorecard import build_scorecard, DriftScorecard


def _collect_reports(store: SnapshotStore) -> Dict:
    reports: Dict = {}
    for source in store.list_sources():
        snapshots = store.load_all(source)
        source_reports = []
        for i in range(1, len(snapshots)):
            report = compare_snapshots(snapshots[i - 1], snapshots[i])
            source_reports.append(report)
        if source_reports:
            reports[source] = source_reports
    return reports


def _print_text(scorecard: DriftScorecard) -> None:
    if not scorecard.entries:
        print("No sources found.")
        return
    header = f"{'Source':<30} {'Versions':>8} {'Drift%':>8} {'Health':>8} {'Added':>6} {'Removed':>7} {'TypeChg':>7}"
    print(header)
    print("-" * len(header))
    for e in sorted(scorecard.entries, key=lambda x: x.health_score):
        drift_pct = f"{e.drift_rate * 100:.1f}%"
        health_pct = f"{e.health_score * 100:.1f}%"
        print(
            f"{e.source:<30} {e.total_versions:>8} {drift_pct:>8} {health_pct:>8}"
            f" {e.added:>6} {e.removed:>7} {e.type_changed:>7}"
        )


def cmd_scorecard(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store_dir)
    reports_by_source = _collect_reports(store)
    scorecard = build_scorecard(reports_by_source)

    if args.format == "json":
        print(json.dumps(scorecard.to_dict(), indent=2))
    else:
        _print_text(scorecard)


def register_scorecard_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("scorecard", help="Show drift health scorecard for all sources")
    p.add_argument("--store-dir", default=".schemadrift", help="Snapshot store directory")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p.set_defaults(func=cmd_scorecard)
