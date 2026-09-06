"""Crossref bibliographic search (free; mailto puts you in the polite pool)."""

from __future__ import annotations

import json
from urllib.parse import quote

from ..bib import Entry
from ..http import HttpClient
from . import Candidate

_BASE = "https://api.crossref.org/works?rows=3&query.bibliographic="


def search(client: HttpClient, entry: Entry, mailto: str = "") -> list[Candidate]:
    url = _BASE + quote(entry.title) + (f"&mailto={mailto}" if mailto else "")
    payload = json.loads(client.get_text(url))
    return [_to_candidate(item) for item in payload.get("message", {}).get("items", [])]


def _to_candidate(item: dict) -> Candidate:
    authors = tuple(_author_name(a) for a in item.get("author", []))
    year = str((item.get("issued", {}).get("date-parts") or [[""]])[0][0])
    venue = (item.get("container-title") or [""])[0]
    return Candidate("crossref", (item.get("title") or [""])[0], authors, year=year, venue=venue,
                     url=item.get("URL", ""))


def _author_name(author: dict) -> str:
    return f"{author.get('given', '')} {author.get('family', '')}".strip()
