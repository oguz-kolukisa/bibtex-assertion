"""Emit corrected BibTeX for entries whose author list disagrees with the verified record."""

from __future__ import annotations

from .bib import Entry
from .normalize import strip_dblp_suffix
from .report import Result

_AUTHOR_PROBLEMS = ("invented_authors", "missing_authors", "misspelled_authors")


def fixable(result: Result) -> bool:
    rules = result.rules
    has_author_problem = any(rules.to_dict()[name] for name in _AUTHOR_PROBLEMS)
    llm_says_authors = bool((result.llm or {}).get("invented_authors"))
    return rules.best is not None and result.verdict != "ok" and (has_author_problem or llm_says_authors)


def fixed_author_field(result: Result) -> str:
    return " and ".join(bibtex_name(strip_dblp_suffix(a)) for a in result.rules.best.authors)


def bibtex_name(name: str) -> str:
    """'First Middle Last' -> 'Last, First Middle'; names already in 'Last, First' form are kept."""
    if "," in name or " " not in name:
        return name
    first, last = name.rsplit(" ", 1)
    return f"{last}, {first}"


def render_entry(entry: Entry, author_field: str) -> str:
    fields = dict(entry.fields)
    fields["author"] = author_field
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items())
    return f"@{entry.entry_type}{{{entry.key},\n{body}\n}}\n"


def fixed_bib(results: list[Result]) -> tuple[str, list[str]]:
    """Return the corrected entries as BibTeX text and the keys that were rewritten."""
    chunks, keys = [], []
    for result in results:
        if result.entry is not None and fixable(result):
            chunks.append(render_entry(result.entry, fixed_author_field(result)))
            keys.append(result.rules.key)
    return "\n".join(chunks), keys
