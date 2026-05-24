"""Tag management for schema snapshots — attach and query metadata tags."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TagEntry:
    source: str
    version: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TagEntry":
        return cls(
            source=data["source"],
            version=data["version"],
            tags=data.get("tags", []),
        )


class TagStore:
    """Persist and query tags associated with snapshot versions."""

    def __init__(self, storage_dir: str) -> None:
        self._root = Path(storage_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def _tag_file(self, source: str) -> Path:
        safe = source.replace("/", "__")
        return self._root / f"{safe}.tags.json"

    def _load_entries(self, source: str) -> Dict[str, TagEntry]:
        path = self._tag_file(source)
        if not path.exists():
            return {}
        with path.open() as f:
            raw = json.load(f)
        return {v: TagEntry.from_dict(d) for v, d in raw.items()}

    def _save_entries(self, source: str, entries: Dict[str, TagEntry]) -> None:
        path = self._tag_file(source)
        with path.open("w") as f:
            json.dump({v: e.to_dict() for v, e in entries.items()}, f, indent=2)

    def set_tags(self, source: str, version: str, tags: List[str]) -> TagEntry:
        entries = self._load_entries(source)
        entry = TagEntry(source=source, version=version, tags=list(tags))
        entries[version] = entry
        self._save_entries(source, entries)
        return entry

    def get_tags(self, source: str, version: str) -> Optional[TagEntry]:
        entries = self._load_entries(source)
        return entries.get(version)

    def find_by_tag(self, source: str, tag: str) -> List[TagEntry]:
        entries = self._load_entries(source)
        return [e for e in entries.values() if tag in e.tags]

    def list_all(self, source: str) -> List[TagEntry]:
        entries = self._load_entries(source)
        return sorted(entries.values(), key=lambda e: e.version)

    def delete_tags(self, source: str, version: str) -> bool:
        entries = self._load_entries(source)
        if version not in entries:
            return False
        del entries[version]
        self._save_entries(source, entries)
        return True
