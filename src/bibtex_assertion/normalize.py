"""Pure text-normalization helpers shared by the parser, the sources and the comparator."""

from __future__ import annotations

import re
import unicodedata

_LATEX_ACCENT = re.compile(r"\\[`'^\"~=.uvHcdb]\s*\{?([A-Za-z])\}?")
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+\s*")
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_STOPWORDS = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "via", "by", "is", "are"}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def clean_latex(text: str) -> str:
    """Remove LaTeX accent macros, commands and braces from a field value."""
    text = _LATEX_ACCENT.sub(r"\1", text)
    text = _LATEX_COMMAND.sub("", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(text: str) -> str:
    """Lowercase ASCII with only letters, digits and single spaces."""
    lowered = strip_accents(clean_latex(text)).lower()
    return re.sub(r"\s+", " ", _NON_ALNUM.sub(" ", lowered)).strip()


def title_tokens(title: str) -> set[str]:
    return {tok for tok in normalize_key(title).split() if tok not in _STOPWORDS}


def title_similarity(left: str, right: str) -> float:
    """Jaccard similarity over content words, in [0, 1]."""
    a, b = title_tokens(left), title_tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def surname(full_name: str) -> str:
    """Last token of a 'First Last' name, or the part before the comma in 'Last, First'."""
    name = clean_latex(full_name).strip()
    if "," in name:
        return normalize_key(name.split(",", 1)[0])
    tokens = name.split()
    return normalize_key(tokens[-1]) if tokens else ""


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, ch_l in enumerate(left, 1):
        current = [i]
        for j, ch_r in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ch_l != ch_r)))
        previous = current
    return previous[-1]
