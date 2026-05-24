"""Freeze a schema snapshot to prevent unintended drift from being ignored."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class FreezeEntry:
    source: str
    version: str
    frozen_at: str
    frozen_by: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "frozen_at": self.frozen_at,
            "frozen_by": self.frozen_by,
            "reason": self.reason,
        }

    @staticmethod
    def from_dict(d: dict) -> "FreezeEntry":
        return FreezeEntry(
            source=d["source"],
            version=d["version"],
            frozen_at=d["frozen_at"],
            frozen_by=d["frozen_by"],
            reason=d.get("reason", ""),
        )


class FreezeStore:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _source_path(self, source: str) -> str:
        safe = source.replace("/", "_").replace(" ", "_")
        return os.path.join(self._base_dir, f"{safe}_freeze.json")

    def freeze(self, source: str, version: str, frozen_by: str, reason: str = "") -> FreezeEntry:
        entry = FreezeEntry(
            source=source,
            version=version,
            frozen_at=datetime.now(timezone.utc).isoformat(),
            frozen_by=frozen_by,
            reason=reason,
        )
        path = self._source_path(source)
        existing = self._load_all_raw(path)
        existing.append(entry.to_dict())
        with open(path, "w") as f:
            json.dump(existing, f, indent=2)
        return entry

    def unfreeze(self, source: str, version: str) -> bool:
        path = self._source_path(source)
        entries = self._load_all_raw(path)
        filtered = [e for e in entries if e["version"] != version]
        if len(filtered) == len(entries):
            return False
        with open(path, "w") as f:
            json.dump(filtered, f, indent=2)
        return True

    def is_frozen(self, source: str, version: str) -> bool:
        return any(e.version == version for e in self.list_frozen(source))

    def list_frozen(self, source: str) -> list[FreezeEntry]:
        path = self._source_path(source)
        return [FreezeEntry.from_dict(d) for d in self._load_all_raw(path)]

    def _load_all_raw(self, path: str) -> list[dict]:
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return json.load(f)
