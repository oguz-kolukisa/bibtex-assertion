"""LLM adjudication over an OpenAI-compatible endpoint. The LLM never invents facts:
it only reads the BibTeX entry and the records the sources returned."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .bib import Entry
from .compare import Assessment
from .criteria import CRITERIA
from .sources import Candidate

_SYSTEM = (
    "You audit bibliography entries for a machine-learning conference. You are given one BibTeX entry and "
    "the records that public scholarly databases returned for its title. Judge ONLY from those records. "
    "Never rely on your own memory of papers. Answer with a single JSON object and nothing else."
)
_CONVENTIONS = """\
Conventions: an author field ending in 'and others' deliberately truncates the list, so authors missing
after the listed ones are NOT an error. Compare the raw author field too: a garbled LaTeX accent macro
(e.g. {\\u{A}} standing in for a first name) is a MINOR defect. A wrong first name for a correct surname
counts as an added non-author (HALLUCINATED). A wrong surname is an added non-author, not a misspelling,
unless it is within one or two letters of the real one.
An arXiv record is a preprint, never evidence about the published venue: if the entry cites a conference
or journal and the only record is arXiv, treat the venue as unverified, not wrong. Flag a venue only when
a record from a publisher database (OpenAlex, Crossref, DBLP) shows a different published venue. A year
that differs from the arXiv year but matches the published venue's year is correct.
"""
_SCHEMA = {
    "exists": "true|false", "matching_record": "index into records or null",
    "author_verdict": "exact|minor|hallucinated", "invented_authors": ["names in the entry that are not on the paper"],
    "missing_authors": ["real authors absent from the entry"], "venue_year_ok": "true|false",
    "verdict": "ok|minor|hallucinated|unverifiable", "explanation": "one or two sentences",
}


@dataclass
class LlmConfig:
    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls) -> "LlmConfig | None":
        model = os.environ.get("LLM_MODEL")
        if not model:
            return None
        return cls(os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
                   os.environ.get("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "")), model)


class Judge:
    def __init__(self, config: LlmConfig):
        from openai import OpenAI  # imported lazily so --no-llm needs no client

        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key or "none")
        self.model = config.model

    def adjudicate(self, entry: Entry, candidates: list[Candidate], rules: Assessment) -> dict:
        response = self.client.chat.completions.create(
            model=self.model, temperature=0,
            messages=[{"role": "system", "content": _SYSTEM},
                      {"role": "user", "content": build_prompt(entry, candidates, rules)}])
        return parse_json(response.choices[0].message.content or "")


def build_prompt(entry: Entry, candidates: list[Candidate], rules: Assessment) -> str:
    return "\n\n".join([
        "CRITERIA:\n" + CRITERIA + _CONVENTIONS,
        "BIBTEX ENTRY (key %s):\n%s" % (entry.key, json.dumps(_entry_view(entry), indent=1)),
        "RECORDS FROM DATABASES:\n" + json.dumps([c.to_dict() for c in candidates[:6]], indent=1),
        "RULE-BASED PRECHECK (surname matching, may be wrong on name variants):\n" + json.dumps(rules.to_dict(), indent=1),
        "Respond with JSON of this shape:\n" + json.dumps(_SCHEMA, indent=1),
    ])


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if match is None:
        return {"verdict": "unverifiable", "explanation": "LLM returned no JSON: " + text[:200]}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"verdict": "unverifiable", "explanation": "LLM returned malformed JSON: " + text[:200]}


def _entry_view(entry: Entry) -> dict:
    return {"type": entry.entry_type, "title": entry.title, "authors": entry.authors,
            "author_field_raw": entry.fields.get("author", ""), "year": entry.year,
            "venue": entry.venue, "arxiv_id": entry.arxiv_id}
