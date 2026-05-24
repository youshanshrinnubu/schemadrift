"""Watchlist: track specific columns or sources for priority drift monitoring."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class WatchEntry:
    source: str
    column: Optional[str] = None  # None means watch entire source
    reason: str = ""

    def to_dict(self) -> dict:
        return {"source": self.source, "column": self.column, "reason": self.reason}

    @staticmethod
    def from_dict(d: dict) -> "WatchEntry":
        return WatchEntry(
            source=d["source"],
            column=d.get("column"),
            reason=d.get("reason", ""),
        )


@dataclass
class Watchlist:
    entries: List[WatchEntry] = field(default_factory=list)

    def add(self, source: str, column: Optional[str] = None, reason: str = "") -> None:
        entry = WatchEntry(source=source, column=column, reason=reason)
        if not self._exists(source, column):
            self.entries.append(entry)

    def remove(self, source: str, column: Optional[str] = None) -> bool:
        before = len(self.entries)
        self.entries = [
            e for e in self.entries
            if not (e.source == source and e.column == column)
        ]
        return len(self.entries) < before

    def is_watched(self, source: str, column: Optional[str] = None) -> bool:
        return self._exists(source, column) or self._exists(source, None)

    def _exists(self, source: str, column: Optional[str]) -> bool:
        return any(e.source == source and e.column == column for e in self.entries)

    def sources(self) -> List[str]:
        return sorted(set(e.source for e in self.entries))

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @staticmethod
    def from_dict(d: dict) -> "Watchlist":
        return Watchlist(entries=[WatchEntry.from_dict(e) for e in d.get("entries", [])])


class WatchlistStore:
    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self) -> Path:
        return self._base / "watchlist.json"

    def save(self, watchlist: Watchlist) -> None:
        self._path().write_text(json.dumps(watchlist.to_dict(), indent=2))

    def load(self) -> Watchlist:
        p = self._path()
        if not p.exists():
            return Watchlist()
        return Watchlist.from_dict(json.loads(p.read_text()))
