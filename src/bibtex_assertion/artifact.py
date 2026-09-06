"""Entries that cite a web artifact (model card, dataset page, blog post) are checked by URL, not by title."""

from __future__ import annotations

import re

import requests

from .bib import Entry
from .compare import Assessment

_URL = re.compile(r"https?://[^\s}]+")


def artifact_url(entry: Entry) -> str:
    """The first URL in url/howpublished/note, or '' when the entry is not an artifact citation."""
    if entry.entry_type != "misc":
        return ""
    for name in ("url", "howpublished", "note"):
        found = _URL.search(entry.fields.get(name, ""))
        if found:
            return found.group(0).rstrip(".,")
    return ""


def url_resolves(url: str, timeout: float = 20.0) -> bool:
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True,
                                headers={"User-Agent": "Mozilla/5.0 bibtex-assertion"})
        return response.status_code < 400
    except requests.RequestException:
        return False


def assess_artifact(entry: Entry, resolves: bool) -> Assessment:
    verdict = "ok" if resolves else "unverifiable"
    note = f"artifact URL {'resolves' if resolves else 'does not resolve'}: {artifact_url(entry)}"
    return Assessment(entry.key, verdict, None, 0.0, problems=[note])
