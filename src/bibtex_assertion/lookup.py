"""Gather candidate records for an entry from every source, tolerating source failures."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bib import Entry
from .http import HttpClient
from .normalize import title_similarity
from .sources import Candidate, arxiv, crossref, dblp, openalex


@dataclass
class Lookup:
    client: HttpClient
    mailto: str = ""
    errors: list[str] = field(default_factory=list)

    def candidates(self, entry: Entry) -> list[Candidate]:
        found: list[Candidate] = []
        for name, fetch in self._sources():
            found.extend(self._safe(name, fetch, entry))
        return sorted(found, key=lambda c: (-round(title_similarity(entry.title, c.title), 2), c.source == "arxiv"))

    def _sources(self):
        return [
            ("arxiv", lambda e: arxiv.search(self.client, e)),
            ("openalex", lambda e: openalex.search(self.client, e, self.mailto)),
            ("crossref", lambda e: crossref.search(self.client, e, self.mailto)),
            ("dblp", lambda e: dblp.search(self.client, e)),
        ]

    def _safe(self, name: str, fetch, entry: Entry) -> list[Candidate]:
        try:
            return fetch(entry)
        except Exception as exc:  # noqa: BLE001 - a dead source must not stop the run
            self.errors.append(f"{entry.key}/{name}: {exc}")
            return []
