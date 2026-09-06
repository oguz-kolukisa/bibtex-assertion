"""DBLP publication search (free, no key)."""

from __future__ import annotations

import json
from urllib.parse import quote

from ..bib import Entry
from ..http import HttpClient
from . import Candidate

_BASE = "https://dblp.org/search/publ/api?format=json&h=3&q="


def search(client: HttpClient, entry: Entry) -> list[Candidate]:
    payload = json.loads(client.get_text(_BASE + quote(entry.title)))
    hits = payload.get("result", {}).get("hits", {}).get("hit", [])
    return [_to_candidate(hit["info"]) for hit in hits]


def _to_candidate(info: dict) -> Candidate:
    raw = info.get("authors", {}).get("author", [])
    raw = [raw] if isinstance(raw, dict) else raw
    authors = tuple(a.get("text", "") for a in raw)
    return Candidate("dblp", info.get("title", "").rstrip("."), authors, year=info.get("year", ""),
                     venue=info.get("venue", ""), url=info.get("url", ""))
