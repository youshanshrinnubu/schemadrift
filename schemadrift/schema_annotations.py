"""Schema annotations: attach human-readable notes to columns or snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Annotation:
    source: str
    version: str
    column: Optional[str]  # None means snapshot-level annotation
    note: str
    author: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "column": self.column,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Annotation":
        return Annotation(
            source=d["source"],
            version=d["version"],
            column=d.get("column"),
            note=d["note"],
            author=d["author"],
            created_at=d.get("created_at", ""),
        )


class AnnotationStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _source_path(self, source: str) -> str:
        return os.path.join(self.base_dir, "annotations", source + ".json")

    def _load_raw(self, source: str) -> List[dict]:
        path = self._source_path(source)
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            return json.load(f)

    def _save_raw(self, source: str, records: List[dict]) -> None:
        path = self._source_path(source)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(records, f, indent=2)

    def add(self, annotation: Annotation) -> None:
        records = self._load_raw(annotation.source)
        records.append(annotation.to_dict())
        self._save_raw(annotation.source, records)

    def get_for_version(
        self, source: str, version: str
    ) -> List[Annotation]:
        return [
            Annotation.from_dict(r)
            for r in self._load_raw(source)
            if r["version"] == version
        ]

    def get_for_column(
        self, source: str, version: str, column: str
    ) -> List[Annotation]:
        return [
            a
            for a in self.get_for_version(source, version)
            if a.column == column
        ]

    def list_sources(self) -> List[str]:
        base = os.path.join(self.base_dir, "annotations")
        if not os.path.exists(base):
            return []
        return [
            f[:-5] for f in os.listdir(base) if f.endswith(".json")
        ]
