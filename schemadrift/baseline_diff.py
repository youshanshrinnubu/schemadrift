"""Utilities for comparing a snapshot against a named baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from schemadrift.baseline import Baseline, BaselineStore
from schemadrift.drift_detector import DriftReport, compare
from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class BaselineDiffResult:
    baseline_name: str
    source: str
    report: DriftReport
    baseline_version: int
    current_version: int

    @property
    def has_drift(self) -> bool:
        return self.report.has_drift


def diff_against_baseline(
    snapshot: SchemaSnapshot,
    baseline_name: str,
    store: Optional[BaselineStore] = None,
) -> BaselineDiffResult:
    """Compare *snapshot* against the named baseline.

    Raises
    ------
    KeyError
        If no baseline with *baseline_name* exists in *store*.
    ValueError
        If the snapshot source does not match the baseline source.
    """
    if store is None:
        store = BaselineStore()

    baseline = store.load(baseline_name)
    if baseline is None:
        raise KeyError(f"Baseline '{baseline_name}' not found.")

    if baseline.source != snapshot.source:
        raise ValueError(
            f"Source mismatch: baseline has '{baseline.source}', "
            f"snapshot has '{snapshot.source}'."
        )

    report = compare(baseline.snapshot, snapshot)

    return BaselineDiffResult(
        baseline_name=baseline_name,
        source=snapshot.source,
        report=report,
        baseline_version=baseline.snapshot.version,
        current_version=snapshot.version,
    )


def promote_to_baseline(
    snapshot: SchemaSnapshot,
    baseline_name: str,
    store: Optional[BaselineStore] = None,
) -> Baseline:
    """Save *snapshot* as a named baseline, replacing any existing one."""
    if store is None:
        store = BaselineStore()

    baseline = Baseline(
        name=baseline_name,
        source=snapshot.source,
        snapshot=snapshot,
    )
    store.save(baseline)
    return baseline
