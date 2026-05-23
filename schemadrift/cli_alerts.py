"""CLI commands for viewing and managing stored alerts."""

from __future__ import annotations

import argparse
import sys
from typing import List

from schemadrift.alert_engine import Alert
from schemadrift.alert_formatter import format_alerts
from schemadrift.alert_store import AlertStore


def cmd_alerts_list(args: argparse.Namespace) -> None:
    """List all alerts for a source, optionally filtered by version."""
    store = AlertStore(args.store_dir)

    if args.source not in store.list_sources():
        print(f"No alerts found for source '{args.source}'.")
        sys.exit(0)

    if args.version:
        alerts = store.load(args.source, args.version)
        if alerts is None:
            print(f"No alerts found for version '{args.version}'.")
            sys.exit(0)
        pairs: List[tuple] = [(args.version, alerts)]
    else:
        pairs = store.load_all(args.source)

    fmt = getattr(args, "format", "text")
    for version, alerts in pairs:
        print(f"--- {args.source} @ {version} ---")
        print(format_alerts(alerts, fmt))


def cmd_alerts_sources(args: argparse.Namespace) -> None:
    """List all sources that have recorded alerts."""
    store = AlertStore(args.store_dir)
    sources = store.list_sources()
    if not sources:
        print("No alert records found.")
    else:
        for s in sources:
            print(s)


def register_alert_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach alert sub-commands to the main CLI parser."""
    alert_parser = subparsers.add_parser("alerts", help="Manage stored alerts")
    alert_sub = alert_parser.add_subparsers(dest="alert_cmd", required=True)

    # alerts list
    list_parser = alert_sub.add_parser("list", help="List alerts for a source")
    list_parser.add_argument("source", help="Source name")
    list_parser.add_argument("--version", default=None, help="Filter by version")
    list_parser.add_argument(
        "--format", choices=["text", "markdown"], default="text"
    )
    list_parser.add_argument(
        "--store-dir", default=".schemadrift/alerts", dest="store_dir"
    )
    list_parser.set_defaults(func=cmd_alerts_list)

    # alerts sources
    sources_parser = alert_sub.add_parser(
        "sources", help="List sources with recorded alerts"
    )
    sources_parser.add_argument(
        "--store-dir", default=".schemadrift/alerts", dest="store_dir"
    )
    sources_parser.set_defaults(func=cmd_alerts_sources)
