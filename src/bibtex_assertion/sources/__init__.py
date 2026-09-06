"""Scholarly metadata sources. Each exposes search(client, entry) -> list[Candidate]."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Candidate:
    source: str
    title: str
    authors: tuple[str, ...]
    year: str = ""
    venue: str = ""
    url: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"source": self.source, "title": self.title, "authors": list(self.authors),
                "year": self.year, "venue": self.venue, "url": self.url}
