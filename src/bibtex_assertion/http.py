"""Polite HTTP client: caching, per-host pacing and retry on 429/5xx."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from .cache import JsonCache

_RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class HttpClient:
    cache: JsonCache
    user_agent: str
    min_interval: float = 1.0
    retries: int = 3
    _last_call: dict[str, float] = field(default_factory=dict)

    def get_text(self, url: str) -> str:
        cached = self.cache.get(url)
        if cached is not None:
            return cached["text"]
        text = self._fetch(url)
        self.cache.set(url, {"text": text})
        return text

    def _fetch(self, url: str) -> str:
        host = url.split("/")[2]
        for attempt in range(self.retries):
            self._pace(host)
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
            if response.status_code not in _RETRY_STATUSES:
                response.raise_for_status()
                return response.text
            time.sleep(2 ** attempt * 3)
        raise RuntimeError(f"{url}: gave up after {self.retries} attempts (HTTP {response.status_code})")

    def _pace(self, host: str) -> None:
        elapsed = time.monotonic() - self._last_call.get(host, 0.0)
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call[host] = time.monotonic()
