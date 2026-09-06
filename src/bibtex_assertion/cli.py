"""bibtex-assert: verify that every entry in a .bib file is a real, correctly attributed paper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .artifact import artifact_url, assess_artifact, url_resolves
from .bib import Entry, parse_bib
from .cache import JsonCache
from .compare import assess
from .http import HttpClient
from .judge import Judge, LlmConfig
from .lookup import Lookup
from .report import Result, to_json, to_markdown


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    entries = _select(parse_bib(Path(args.bib).read_text(encoding="utf-8")), args.only)
    results = run(entries, args)
    _write_outputs(results, args)
    return 1 if any(r.verdict == "hallucinated" for r in results) else 0


def run(entries: list[Entry], args: argparse.Namespace) -> list[Result]:
    lookup = Lookup(_client(args), args.mailto)
    judge = _judge(args)
    results = []
    for entry in entries:
        results.append(_check_one(entry, lookup, judge))
        _progress(results[-1])
    return results


def _check_one(entry: Entry, lookup: Lookup, judge: Judge | None) -> Result:
    url = artifact_url(entry)
    if url:
        return Result(assess_artifact(entry, url_resolves(url)), entry=entry)
    candidates = lookup.candidates(entry)
    rules = assess(entry, candidates)
    llm = _adjudicate(judge, entry, candidates, rules)
    errors = [e for e in lookup.errors if e.startswith(entry.key + "/")]
    return Result(rules, llm, errors, entry)


def _adjudicate(judge: Judge | None, entry: Entry, candidates, rules) -> dict | None:
    if judge is None:
        return None
    try:
        return judge.adjudicate(entry, candidates, rules)
    except Exception as exc:  # noqa: BLE001 - keep going without the LLM for this entry
        return {"verdict": "unverifiable", "explanation": f"LLM call failed: {exc}"}


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="bibtex-assert", description=__doc__)
    parser.add_argument("bib", help="path to the .bib file")
    parser.add_argument("--only", nargs="*", default=None, help="check only these entry keys")
    parser.add_argument("--no-llm", action="store_true", help="rule-based verdicts only")
    parser.add_argument("--mailto", default="", help="contact email for the OpenAlex/Crossref polite pools")
    parser.add_argument("--cache", default=".cache/bibtex-assertion", help="disk cache directory ('' to disable)")
    parser.add_argument("--json", default=None, help="write the JSON report here")
    parser.add_argument("--md", default=None, help="write the Markdown report here (default: stdout)")
    parser.add_argument("--version", action="version", version=__version__)
    return parser.parse_args(argv)


def _select(entries: list[Entry], only: list[str] | None) -> list[Entry]:
    return entries if not only else [e for e in entries if e.key in set(only)]


def _client(args) -> HttpClient:
    cache = JsonCache(Path(args.cache) if args.cache else None)
    contact = f" (mailto:{args.mailto})" if args.mailto else ""
    return HttpClient(cache, f"bibtex-assertion/{__version__}{contact}")


def _judge(args) -> Judge | None:
    if args.no_llm:
        return None
    config = LlmConfig.from_env()
    if config is None:
        print("LLM_MODEL not set, running rule-based only (use --no-llm to silence this)", file=sys.stderr)
        return None
    return Judge(config)


def _progress(result: Result) -> None:
    print(f"{result.rules.key:<32} {result.verdict}", file=sys.stderr)


def _write_outputs(results: list[Result], args) -> None:
    markdown = to_markdown(results)
    if args.md:
        Path(args.md).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json:
        Path(args.json).write_text(to_json(results), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
