"""Polite HTTP client: caching, per-host pacing, Retry-After aware retries and a per-host circuit breaker."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from .cache import JsonCache

_RETRY_STATUSES = {429, 500, 502, 503, 504}


class SourceUnavailable(RuntimeError):
    """Raised when a host has failed too often in this run and is being skipped."""


@dataclass
class HttpClient:
    cache: JsonCache
    user_agent: str
    min_interval: float = 1.0
    retries: int = 2
    max_wait: float = 20.0
    trip_after: int = 3
    _last_call: dict[str, float] = field(default_factory=dict)
    _failures: dict[str, int] = field(default_factory=dict)

    def get_text(self, url: str) -> str:
        cached = self.cache.get(url)
        if cached is not None:
            return cached["text"]
        text = self._fetch(url)
        self.cache.set(url, {"text": text})
        return text

    def _fetch(self, url: str) -> str:
        host = url.split("/")[2]
        self._ensure_open(host)
        for attempt in range(self.retries + 1):
            response = self._request(url, host)
            if response.status_code not in _RETRY_STATUSES:
                response.raise_for_status()
                self._failures[host] = 0
                return response.text
            self._back_off(response, attempt)
        return self._give_up(host, url, response.status_code)

    def _request(self, url: str, host: str) -> requests.Response:
        self._pace(host)
        return requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)

    def _back_off(self, response: requests.Response, attempt: int) -> None:
        advised = response.headers.get("Retry-After")
        wait = float(advised) if advised and advised.isdigit() else 2.0 * (2 ** attempt)
        time.sleep(min(wait, self.max_wait))

    def _give_up(self, host: str, url: str, status: int) -> str:
        self._failures[host] = self._failures.get(host, 0) + 1
        raise RuntimeError(f"{url}: HTTP {status} after {self.retries + 1} attempts")

    def _ensure_open(self, host: str) -> None:
        if self._failures.get(host, 0) >= self.trip_after:
            raise SourceUnavailable(f"{host}: skipped after {self.trip_after} consecutive failures")

    def _pace(self, host: str) -> None:
        elapsed = time.monotonic() - self._last_call.get(host, 0.0)
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call[host] = time.monotonic()
