# bibtex-assertion — agent instructions

Checks that BibTeX entries are real and correctly attributed using free scholarly APIs plus an optional
LLM adjudicator.

## Orientation

- Read `README.md` first.
- Entry point: `src/bibtex_assertion/cli.py` (`uv run bibtex-assert file.bib`).

## Build / run

```bash
uv sync --extra dev
uv run pytest              # offline tests
uv run pytest -m network   # live API tests
uv run bibtex-assert tests/fixtures/probe_bad7.bib --no-llm
```

## Rules

- No secrets in the repo. LLM credentials come from `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
- The LLM must never be the source of bibliographic facts. Facts come from the sources; the LLM only judges.
- Commits: concise human style, no Claude/AI attribution.
- New functions need unit tests. Bump the version in `pyproject.toml` and `__init__.py` before a
  user-visible commit.
- Code follows the Clean Code rules (playbook/rules/clean-code.md): one job per function, at most
  ~20 lines, at most three arguments, no side effects in pure modules (`bib`, `normalize`, `compare`, `report`).
- Prose follows playbook/rules/writing-style-en.md.
