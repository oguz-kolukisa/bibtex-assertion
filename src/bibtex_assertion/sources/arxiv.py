"""arXiv Atom API: exact lookup by id, otherwise a title search."""

from __future__ import annotations

import re
from urllib.parse import quote

from ..bib import Entry
from ..http import HttpClient
from . import Candidate

_BASE = "https://export.arxiv.org/api/query?"


def search(client: HttpClient, entry: Entry) -> list[Candidate]:
    xml = client.get_text(_query_url(entry))
    return [_to_candidate(block) for block in re.findall(r"<entry>.*?</entry>", xml, re.S)]


def _query_url(entry: Entry) -> str:
    if entry.arxiv_id:
        return _BASE + "id_list=" + entry.arxiv_id
    return _BASE + "search_query=ti:%22" + quote(entry.title) + "%22&max_results=3"


def _to_candidate(block: str) -> Candidate:
    title = _tag(block, "title")
    authors = tuple(re.findall(r"<name>(.*?)</name>", block, re.S))
    return Candidate("arxiv", title, authors, year=_tag(block, "published")[:4],
                     venue="arXiv", url=_tag(block, "id"))


def _tag(block: str, name: str) -> str:
    found = re.search(rf"<{name}>(.*?)</{name}>", block, re.S)
    return re.sub(r"\s+", " ", found.group(1)).strip() if found else ""
