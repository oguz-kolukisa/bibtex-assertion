"""OpenAlex works search by title (free, no key; mailto enables the polite pool)."""

from __future__ import annotations

import json
from urllib.parse import quote

from ..bib import Entry
from ..http import HttpClient
from . import Candidate

_BASE = "https://api.openalex.org/works?per-page=3&filter=title.search:"


def search(client: HttpClient, entry: Entry, mailto: str = "") -> list[Candidate]:
    url = _BASE + quote(_safe_title(entry.title)) + (f"&mailto={mailto}" if mailto else "")
    payload = json.loads(client.get_text(url))
    return [_to_candidate(work) for work in payload.get("results", [])]


def _safe_title(title: str) -> str:
    """OpenAlex rejects some punctuation in filter values."""
    return "".join(ch if ch.isalnum() or ch == " " else " " for ch in title)[:200]


def _to_candidate(work: dict) -> Candidate:
    authors = tuple(a["author"]["display_name"] for a in work.get("authorships", []))
    venue = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    return Candidate("openalex", work.get("title") or "", authors,
                     year=str(work.get("publication_year") or ""), venue=venue, url=work.get("doi") or work.get("id", ""))
