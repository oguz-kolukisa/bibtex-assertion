"""Render assertion results as Markdown and JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .compare import Assessment

_ICON = {"ok": "PASS", "minor": "MINOR", "hallucinated": "HALLUCINATED", "unverifiable": "UNVERIFIABLE"}
_SEVERITY = {"ok": 0, "unverifiable": 1, "minor": 2, "hallucinated": 3}


@dataclass
class Result:
    rules: Assessment
    llm: dict | None = None
    errors: list[str] = field(default_factory=list)

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
    lines = ["# BibTeX assertion report", "", _summary_line(results), "",
             "| Key | Verdict | Problems | Best match |", "|---|---|---|---|"]
    lines.extend(_row(r) for r in results)
    return "\n".join(lines) + "\n"


def _summary_line(results: list[Result]) -> str:
    counts = {label: sum(1 for r in results if r.verdict == label) for label in _ICON}
    return " · ".join(f"{_ICON[label]}: {n}" for label, n in counts.items() if n) or "no entries"


def _row(result: Result) -> str:
    problems = "; ".join(_problems(result)) or "-"
    best = result.rules.best
    match = f"{best.source}: {best.title[:60]} ({best.year})" if best else "none"
    return f"| `{result.rules.key}` | {_ICON[result.verdict]} | {problems} | {match} |"


def _problems(result: Result) -> list[str]:
    problems = list(result.rules.problems)
    if result.llm and result.llm.get("explanation"):
        problems.append("LLM: " + str(result.llm["explanation"]))
    if result.disagreement:
        problems.append(f"rules said {result.rules.verdict}, LLM said {result.llm['verdict']}")
    return [p.replace("|", "/") for p in problems]
