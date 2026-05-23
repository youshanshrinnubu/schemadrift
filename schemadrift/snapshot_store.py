"""Persistence layer for schema snapshots — save and load snapshots to/from disk."""

import json
import os
from datetime import datetime
from typing import List, Optional

from schemadrift.schema_snapshot import SchemaSnapshot


class SnapshotStore:
    """Manages reading and writing SchemaSnapshot objects to a local JSON store."""

    def __init__(self, store_dir: str = ".schemadrift"):
        self.store_dir = store_dir
        os.makedirs(self.store_dir, exist_ok=True)

    def _source_path(self, source_name: str) -> str:
        safe_name = source_name.replace("/", "_").replace(" ", "_")
        return os.path.join(self.store_dir, f"{safe_name}.json")

    def save(self, snapshot: SchemaSnapshot) -> None:
        """Append a snapshot to the store for its source."""
        path = self._source_path(snapshot.source_name)
        snapshots = self.load_all(snapshot.source_name)
        snapshots.append(snapshot)
        with open(path, "w") as f:
            json.dump([s.to_dict() for s in snapshots], f, indent=2)

    def load_all(self, source_name: str) -> List[SchemaSnapshot]:
        """Load all snapshots for a given source, ordered by captured_at."""
        path = self._source_path(source_name)
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            raw = json.load(f)
        snapshots = [SchemaSnapshot.from_dict(d) for d in raw]
        snapshots.sort(key=lambda s: s.captured_at)
        return snapshots

    def load_latest(self, source_name: str) -> Optional[SchemaSnapshot]:
        """Return the most recent snapshot for a source, or None if none exist."""
        snapshots = self.load_all(source_name)
        return snapshots[-1] if snapshots else None

    def load_at_version(self, source_name: str, version: str) -> Optional[SchemaSnapshot]:
        """Return the snapshot matching a specific version string."""
        for snapshot in self.load_all(source_name):
            if snapshot.version == version:
                return snapshot
        return None

    def list_sources(self) -> List[str]:
        """Return all source names that have stored snapshots."""
        sources = []
        for fname in os.listdir(self.store_dir):
            if fname.endswith(".json"):
                sources.append(fname[:-5])
        return sorted(sources)

    def delete(self, source_name: str) -> bool:
        """Delete all snapshots for a source. Returns True if file existed."""
        path = self._source_path(source_name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
