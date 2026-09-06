"""Tiny JSON file cache so re-runs do not hammer the public APIs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class JsonCache:
    def __init__(self, directory: Path | None):
        self.directory = directory
        if directory is not None:
            directory.mkdir(parents=True, exist_ok=True)

    def get(self, url: str):
        path = self._path(url)
        if path is None or not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, url: str, payload) -> None:
        path = self._path(url)
        if path is not None:
            path.write_text(json.dumps(payload), encoding="utf-8")

    def _path(self, url: str) -> Path | None:
        if self.directory is None:
            return None
        return self.directory / (hashlib.sha1(url.encode()).hexdigest() + ".json")
