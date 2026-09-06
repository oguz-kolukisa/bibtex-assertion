"""Rule-based comparison of a BibTeX entry with the best candidate record. Pure functions only."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bib import Entry, has_et_al
from .normalize import edit_distance, surname, title_similarity
from .sources import Candidate

TITLE_MATCH = 0.6
ARTIFACT_TITLE_MATCH = 0.9
_TYPO_DISTANCE = 2


@dataclass
class Assessment:
    key: str
    verdict: str  # ok | minor | hallucinated | unverifiable
    best: Candidate | None = None
    title_similarity: float = 0.0
    invented_authors: list[str] = field(default_factory=list)
    missing_authors: list[str] = field(default_factory=list)
    misspelled_authors: list[tuple[str, str]] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"key": self.key, "verdict": self.verdict, "title_similarity": round(self.title_similarity, 2),
                "best": self.best.to_dict() if self.best else None, "invented_authors": self.invented_authors,
                "missing_authors": self.missing_authors, "misspelled_authors": self.misspelled_authors,
                "problems": self.problems}


def assess(entry: Entry, candidates: list[Candidate]) -> Assessment:
    best = _best_match(entry, candidates)
    if best is None or _weak_artifact_match(entry, best):
        return _unverifiable(entry, candidates)
    assessment = Assessment(entry.key, "ok", best, title_similarity(entry.title, best.title))
    _check_authors(entry, best, assessment)
    _check_year(entry, _matching_records(entry, candidates), assessment)
    return assessment


def _matching_records(entry: Entry, candidates: list[Candidate]) -> list[Candidate]:
    return [c for c in candidates if title_similarity(entry.title, c.title) >= TITLE_MATCH]


def _best_match(entry: Entry, candidates: list[Candidate]) -> Candidate | None:
    scored = [(title_similarity(entry.title, c.title), c) for c in candidates if c.authors]
    scored = [(s, c) for s, c in scored if s >= TITLE_MATCH]
    if not scored:
        return None
    return max(scored, key=lambda pair: (pair[0], len(pair[1].authors)))[1]


def _weak_artifact_match(entry: Entry, best: Candidate) -> bool:
    """A model card or dataset page rarely has a scholarly record; demand a near-exact title."""
    return _is_artifact(entry) and title_similarity(entry.title, best.title) < ARTIFACT_TITLE_MATCH


def _unverifiable(entry: Entry, candidates: list[Candidate]) -> Assessment:
    verdict = "unverifiable" if not entry.title or _is_artifact(entry) else "hallucinated"
    note = "no source returned a document with a matching title" if candidates or entry.title else "no title"
    return Assessment(entry.key, verdict, None, 0.0, problems=[note])


def _is_artifact(entry: Entry) -> bool:
    return entry.entry_type == "misc" and bool(entry.fields.get("howpublished") or entry.fields.get("url"))


def _check_authors(entry: Entry, best: Candidate, out: Assessment) -> None:
    bib, real = [surname(a) for a in entry.authors], [surname(a) for a in best.authors]
    _diff_surnames(bib, real, out)
    truncated = has_et_al(entry.fields.get("author", ""))
    if out.invented_authors or (_missing_fraction(out, real) > 0.5 and not truncated):
        out.verdict = "hallucinated"
    elif out.misspelled_authors or (out.missing_authors and not truncated):
        out.verdict = "minor"
    _note_problems(entry, out, truncated)


def _diff_surnames(bib: list[str], real: list[str], out: Assessment) -> None:
    unmatched_real = list(real)
    for name in bib:
        match = _closest(name, unmatched_real)
        if match is None:
            out.invented_authors.append(name)
            continue
        unmatched_real.remove(match)
        if match != name and not _is_substring(name, match):
            out.misspelled_authors.append((name, match))
    out.missing_authors = unmatched_real


def _closest(name: str, pool: list[str]) -> str | None:
    if name in pool:
        return name
    near = [p for p in pool if _looks_like_typo(name, p) or _is_substring(name, p)]
    return min(near, key=lambda p: edit_distance(name, p)) if near else None


def _looks_like_typo(name: str, other: str) -> bool:
    """Same initial and a small edit distance relative to the length (Cadene/Cadène, Viegas/Viégas)."""
    budget = 1 if len(name) <= 4 else _TYPO_DISTANCE
    return name[:1] == other[:1] and edit_distance(name, other) <= budget


def _is_substring(name: str, other: str) -> bool:
    """Compound surnames written in one part (Rott Shaham / Shaham, Lopez-Paz / Lopez Paz)."""
    shorter, longer = sorted((name, other), key=len)
    return len(shorter) >= 4 and shorter in longer


def _missing_fraction(out: Assessment, real: list[str]) -> float:
    return len(out.missing_authors) / len(real) if real else 0.0


def _note_problems(entry: Entry, out: Assessment, truncated: bool) -> None:
    if out.missing_authors and truncated:
        out.problems.append("author list truncated with 'and others' / 'et al.'")
    elif out.missing_authors:
        out.problems.append("missing authors: " + ", ".join(out.missing_authors))
    for bad in out.invented_authors:
        out.problems.append(f"author '{bad}' is not on the paper")
    for bib_name, real_name in out.misspelled_authors:
        out.problems.append(f"author '{bib_name}' should be '{real_name}'")


def _check_year(entry: Entry, records: list[Candidate], out: Assessment) -> None:
    """A preprint year differing from the published year is normal, so any record may vouch for the year."""
    years = {r.year for r in records if r.year.isdigit()}
    if not entry.year.isdigit() or not years or any(abs(int(entry.year) - int(y)) <= 1 for y in years):
        return
    out.problems.append(f"year {entry.year} vs {'/'.join(sorted(years))} in the records")
    if out.verdict == "ok":
        out.verdict = "minor"
