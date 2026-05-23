"""Baseline management for schema drift detection.

A baseline is a named, pinned snapshot that serves as the reference
point for drift comparisons, independent of the normal version history.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class Baseline:
    name: str
    source: str
    snapshot: SchemaSnapshot

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "snapshot": self.snapshot.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        return cls(
            name=data["name"],
            source=data["source"],
            snapshot=SchemaSnapshot.from_dict(data["snapshot"]),
        )


class BaselineStore:
    """Persists named baselines to a JSON file on disk."""

    def __init__(self, directory: str = ".schemadrift") -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self._path = os.path.join(directory, "baselines.json")

    def _load_raw(self) -> dict:
        if not os.path.exists(self._path):
            return {}
        with open(self._path, "r") as fh:
            return json.load(fh)

    def _save_raw(self, data: dict) -> None:
        with open(self._path, "w") as fh:
            json.dump(data, fh, indent=2)

    def save(self, baseline: Baseline) -> None:
        raw = self._load_raw()
        raw[baseline.name] = baseline.to_dict()
        self._save_raw(raw)

    def load(self, name: str) -> Optional[Baseline]:
        raw = self._load_raw()
        if name not in raw:
            return None
        return Baseline.from_dict(raw[name])

    def list_names(self) -> list[str]:
        return sorted(self._load_raw().keys())

    def delete(self, name: str) -> bool:
        raw = self._load_raw()
        if name not in raw:
            return False
        del raw[name]
        self._save_raw(raw)
        return True
