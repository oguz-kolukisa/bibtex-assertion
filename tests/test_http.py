from unittest.mock import patch

import pytest

from bibtex_assertion.cache import JsonCache
from bibtex_assertion.http import HttpClient, SourceUnavailable


class _Resp:
    def __init__(self, status, text="x", headers=None):
        self.status_code, self.text, self.headers = status, text, headers or {}

    def raise_for_status(self):
        pass


def _client():
    return HttpClient(JsonCache(None), "test", min_interval=0, retries=1, max_wait=0, trip_after=2)


def test_returns_text_and_caches_nothing_without_dir():
    with patch("bibtex_assertion.http.requests.get", return_value=_Resp(200, "ok")):
        assert _client().get_text("https://h.example/a") == "ok"


def test_retries_then_raises_and_trips_the_breaker():
    client = _client()
    with patch("bibtex_assertion.http.requests.get", return_value=_Resp(429)), patch("bibtex_assertion.http.time.sleep"):
        with pytest.raises(RuntimeError):
            client.get_text("https://h.example/a")
        with pytest.raises(RuntimeError):
            client.get_text("https://h.example/b")
        with pytest.raises(SourceUnavailable):
            client.get_text("https://h.example/c")


def test_success_resets_failure_count():
    client = _client()
    with patch("bibtex_assertion.http.requests.get", side_effect=[_Resp(503), _Resp(503), _Resp(200, "fine")]), \
         patch("bibtex_assertion.http.time.sleep"):
        with pytest.raises(RuntimeError):
            client.get_text("https://h.example/a")
        assert client.get_text("https://h.example/b") == "fine"
        assert client._failures["h.example"] == 0
