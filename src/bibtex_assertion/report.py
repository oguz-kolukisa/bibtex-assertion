"""Render assertion results as Markdown and JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .bib import Entry
from .compare import Assessment

_ICON = {"ok": "PASS", "minor": "MINOR", "hallucinated": "HALLUCINATED", "unverifiable": "UNVERIFIABLE"}
_SEVERITY = {"ok": 0, "unverifiable": 1, "minor": 2, "hallucinated": 3}


@dataclass
class Result:
    rules: Assessment
    llm: dict | None = None
    errors: list[str] = field(default_factory=list)
    entry: Entry | None = None

    @property
    def verdict(self) -> str:
        """The stricter of the rule-based and the LLM verdict, so neither judge can hide a problem."""
        llm_verdict = (self.llm or {}).get("verdict")
        if llm_verdict not in _ICON:
            return self.rules.verdict
        return max(self.rules.verdict, llm_verdict, key=_SEVERITY.__getitem__)

    @property
    def disagreement(self) -> bool:
        return bool(self.llm) and self.llm.get("verdict") in _ICON and self.llm["verdict"] != self.rules.verdict

    def to_dict(self) -> dict:
        return {"key": self.rules.key, "verdict": self.verdict, "rules": self.rules.to_dict(), "llm": self.llm,
                "disagreement": self.disagreement, "errors": self.errors}


def to_json(results: list[Result]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=1, ensure_ascii=False)


def to_markdown(results: list[Result]) -> str:
    flagged = [r for r in results if r.verdict != "ok"]
    passed = [r for r in results if r.verdict == "ok"]
    lines = ["# BibTeX assertion report", "", *_summary(results), ""]
    lines.extend(_problem_table(flagged))
    lines.extend(["", "## Passed", "", ", ".join(f"`{r.rules.key}`" for r in passed) or "none", ""])
    return "\n".join(lines)


def _summary(results: list[Result]) -> list[str]:
    counts = {label: sum(1 for r in results if r.verdict == label) for label in _ICON}
    lines = [f"- Entries checked: **{len(results)}**"]
    lines.extend(f"- {_ICON[label]}: **{n}**" for label, n in counts.items())
    return lines


def _problem_table(flagged: list[Result]) -> list[str]:
    if not flagged:
        return ["No problems found."]
    header = ["## Problems", "", "| Key | Verdict | Ours (BibTeX) | Real (best record) | Rule-based diff | LLM comment |",
              "|---|---|---|---|---|---|"]
    return header + [_row(r) for r in flagged]


def _row(r: Result) -> str:
    cells = [f"`{r.rules.key}`", _ICON[r.verdict], _ours(r), _real(r), _diff(r), _llm_comment(r)]
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def _ours(r: Result) -> str:
    if r.entry is None:
        return "-"
    return f"{r.entry.title} — {'; '.join(r.entry.authors) or 'no authors'} — {r.entry.venue or 'no venue'} {r.entry.year}"


def _real(r: Result) -> str:
    best = r.rules.best
    if best is None:
        return "no matching record" if not r.rules.problems else r.rules.problems[0]
    return f"{best.title} — {'; '.join(best.authors)} — {best.venue or best.source} {best.year} ({best.source})"


def _diff(r: Result) -> str:
    problems = [p for p in r.rules.problems if not p.startswith("artifact URL")]
    return "; ".join(problems) or "-"


def _llm_comment(r: Result) -> str:
    if not r.llm:
        return "(no LLM)"
    comment = str(r.llm.get("explanation", "")).strip() or "(no comment)"
    if r.disagreement:
        comment += f" [rules: {r.rules.verdict}, LLM: {r.llm['verdict']}]"
    return comment


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")
