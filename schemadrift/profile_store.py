"""Persistence layer for SchemaProfile objects."""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional

from schemadrift.column_profile import SchemaProfile


class ProfileStore:
    def __init__(self, base_dir: str = ".schemadrift/profiles") -> None:
        self.base_dir = Path(base_dir)

    def _source_path(self, source: str) -> Path:
        safe = source.replace("/", "_").replace(" ", "_")
        return self.base_dir / safe

    def save(self, profile: SchemaProfile) -> None:
        path = self._source_path(profile.source)
        path.mkdir(parents=True, exist_ok=True)
        file = path / f"{profile.version}.json"
        file.write_text(json.dumps(profile.to_dict(), indent=2))

    def load(self, source: str, version: str) -> Optional[SchemaProfile]:
        file = self._source_path(source) / f"{version}.json"
        if not file.exists():
            return None
        return SchemaProfile.from_dict(json.loads(file.read_text()))

    def load_all(self, source: str) -> List[SchemaProfile]:
        path = self._source_path(source)
        if not path.exists():
            return []
        profiles = []
        for f in sorted(path.glob("*.json")):
            profiles.append(SchemaProfile.from_dict(json.loads(f.read_text())))
        return profiles

    def load_latest(self, source: str) -> Optional[SchemaProfile]:
        all_profiles = self.load_all(source)
        return all_profiles[-1] if all_profiles else None

    def list_versions(self, source: str) -> List[str]:
        path = self._source_path(source)
        if not path.exists():
            return []
        return sorted(f.stem for f in path.glob("*.json"))

    def delete(self, source: str, version: str) -> bool:
        file = self._source_path(source) / f"{version}.json"
        if file.exists():
            file.unlink()
            return True
        return False
