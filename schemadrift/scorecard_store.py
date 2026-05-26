from __future__ import annotations
import json
import os
from typing import Optional
from schemadrift.schema_diff_scorecard import DriftScorecard, ScorecardEntry


class ScorecardStore:
    """Persists scorecard snapshots keyed by run timestamp/version."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, version: str) -> str:
        safe = version.replace(":", "-").replace(" ", "_")
        return os.path.join(self._base_dir, f"scorecard_{safe}.json")

    def save(self, version: str, scorecard: DriftScorecard) -> None:
        with open(self._path(version), "w") as fh:
            json.dump({"version": version, **scorecard.to_dict()}, fh, indent=2)

    def load(self, version: str) -> Optional[DriftScorecard]:
        path = self._path(version)
        if not os.path.exists(path):
            return None
        with open(path) as fh:
            data = json.load(fh)
        return _scorecard_from_dict(data)

    def list_versions(self) -> list:
        files = sorted(
            f for f in os.listdir(self._base_dir) if f.startswith("scorecard_") and f.endswith(".json")
        )
        return [f[len("scorecard_"):-len(".json")].replace("_", " ") for f in files]

    def load_latest(self) -> Optional[DriftScorecard]:
        versions = self.list_versions()
        if not versions:
            return None
        return self.load(versions[-1])


def _scorecard_from_dict(data: dict) -> DriftScorecard:
    entries = [
        ScorecardEntry(
            source=e["source"],
            total_versions=e["total_versions"],
            versions_with_drift=e["versions_with_drift"],
            total_changes=e["total_changes"],
            added=e["added"],
            removed=e["removed"],
            type_changed=e["type_changed"],
            drift_rate=e["drift_rate"],
            health_score=e["health_score"],
        )
        for e in data.get("entries", [])
    ]
    return DriftScorecard(entries=entries)
