"""Minimal BibTeX reader: entries, fields, authors and arXiv ids. No external dependency."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .normalize import clean_latex

_ENTRY_START = re.compile(r"^\s*@(?P<type>[A-Za-z]+)\s*\{", re.M)
_ARXIV_ID = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
_VENUE_FIELDS = ("booktitle", "journal", "howpublished", "publisher")


@dataclass(frozen=True)
class Entry:
    key: str
    entry_type: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def title(self) -> str:
        return clean_latex(self.fields.get("title", ""))

    @property
    def authors(self) -> list[str]:
        return split_authors(self.fields.get("author", ""))

    @property
    def year(self) -> str:
        return self.fields.get("year", "").strip()

    @property
    def venue(self) -> str:
        for name in _VENUE_FIELDS:
            if self.fields.get(name):
                return clean_latex(self.fields[name])
        return ""

    @property
    def arxiv_id(self) -> str:
        for name in ("eprint", "journal", "note", "url", "howpublished"):
            found = _ARXIV_ID.search(self.fields.get(name, ""))
            if found:
                return found.group(1)
        return ""


def parse_bib(text: str) -> list[Entry]:
    """Parse every @entry in a .bib string, skipping @string/@comment/@preamble."""
    entries = []
    for chunk in _split_entries(text):
        entry = _parse_entry(chunk)
        if entry is not None:
            entries.append(entry)
    return entries


def split_authors(author_field: str) -> list[str]:
    parts = re.split(r"\s+and\s+", clean_latex(author_field))
    return [p.strip() for p in parts if p.strip() and p.strip().lower() != "others"]


def has_et_al(author_field: str) -> bool:
    return bool(re.search(r"\band\s+others\b|et al", author_field))


def _split_entries(text: str) -> list[str]:
    starts = [m.start() for m in _ENTRY_START.finditer(text)]
    starts.append(len(text))
    return [text[a:b] for a, b in zip(starts, starts[1:])]


def _parse_entry(chunk: str) -> Entry | None:
    head = _ENTRY_START.match(chunk)
    if head is None or head.group("type").lower() in {"string", "comment", "preamble"}:
        return None
    body = _entry_body(chunk[head.end():])
    key, _, rest = body.partition(",")
    return Entry(key.strip(), head.group("type").lower(), _parse_fields(rest))


def _entry_body(text: str) -> str:
    """Return the text up to the brace that closes the entry."""
    depth = 1
    for i, ch in enumerate(text):
        depth += (ch == "{") - (ch == "}")
        if depth == 0:
            return text[:i]
    return text


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for name, value in _iter_fields(body):
        fields[name.lower()] = value
    return fields


def _iter_fields(body: str):
    position = 0
    while True:
        match = re.compile(r"\s*([A-Za-z_-]+)\s*=\s*").match(body, position)
        if match is None:
            return
        value, position = _read_value(body, match.end())
        yield match.group(1), value
        position = _skip_comma(body, position)


def _read_value(body: str, start: int) -> tuple[str, int]:
    if start < len(body) and body[start] == "{":
        return _read_braced(body, start)
    if start < len(body) and body[start] == '"':
        end = body.find('"', start + 1)
        return body[start + 1:end], end + 1
    end = re.compile(r"[,\n]").search(body, start)
    stop = end.start() if end else len(body)
    return body[start:stop].strip(), stop


def _read_braced(body: str, start: int) -> tuple[str, int]:
    depth = 0
    for i in range(start, len(body)):
        depth += (body[i] == "{") - (body[i] == "}")
        if depth == 0:
            return body[start + 1:i], i + 1
    return body[start + 1:], len(body)


def _skip_comma(body: str, position: int) -> int:
    match = re.compile(r"\s*,?").match(body, position)
    return match.end() if match else position
