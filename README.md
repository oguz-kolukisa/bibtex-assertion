# bibtex-assertion

Assert that every entry in a `.bib` file describes a real paper with the right authors, venue and year.

Verdicts follow the hallucinated-reference criteria published by the ICLR, ICML and NeurIPS 2026 program
chairs (`src/bibtex_assertion/criteria.py`).

## How it works

1. **Look up facts** from free scholarly APIs, never from an LLM's memory: arXiv (by id when the entry
   has one, otherwise by title), OpenAlex, Crossref and DBLP. Results are cached on disk and requests are
   paced with retry on 429/5xx.
2. **Compare deterministically**: best title match, then surname-level author diff. Invented authors or
   more than half the authors missing → `hallucinated`; small misspellings, a few missing authors, or a
   year off by more than one → `minor`; nothing found under a matching title → `hallucinated`
   (or `unverifiable` for `@misc` artifacts such as model cards and blog posts).
3. **Adjudicate with an LLM** (optional): the entry, the returned records and the rule-based precheck are
   handed to any OpenAI-compatible model with the criteria text. The LLM is instructed to judge only from the
   records, and its job is the part surnames cannot do: wrong first names (`Zhicheng Zhao` for `Qiming Zhao`),
   name variants, and explaining the discrepancy. When the LLM and the rules disagree the report says so.

Exit code is 1 if any entry is `hallucinated`, so it works as a pre-submission gate.

## Install and run

```bash
uv sync
uv run bibtex-assert paper.bib --mailto you@example.com --md report.md --json report.json
uv run bibtex-assert paper.bib --no-llm            # rule-based only, no LLM needed
uv run bibtex-assert paper.bib --only key1 key2    # a subset of entries
```

`--mailto` puts you in the OpenAlex and Crossref polite pools (higher rate limits). The cache lives in
`.cache/bibtex-assertion/` by default; pass `--cache ''` to disable it.

## Choosing an LLM (free options)

Set three environment variables. Any OpenAI-compatible chat endpoint works.

```bash
export LLM_BASE_URL=...   # default https://api.openai.com/v1
export LLM_API_KEY=...
export LLM_MODEL=...
```

| Provider | Base URL | Free tier (as of 2026, verify before relying on it) |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | Free keys, no card. Roughly 30 requests/min and 1,000/day on `llama-3.3-70b-versatile`. |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | Free tier on Flash models, no card. Limits shown only in AI Studio after sign-in. |
| OpenRouter | `https://openrouter.ai/api/v1` | Models tagged `:free`. About 20 requests/min and 50/day until $10 of credit is bought. |
| Cerebras, Mistral, Hugging Face | see provider docs | Free tiers exist with daily caps. |
| Ollama (local) | `http://localhost:11434/v1` | Free and offline. `LLM_API_KEY` can be anything. |

A run over a 70-entry bibliography makes about 70 LLM calls, so every free tier above covers it. Sources:
[OpenRouter](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/),
[Novita](https://blogs.novita.ai/free-llm-api-comparison-2026/),
[continuumcode](https://continuumcode.ai/guides/free-llm-api/).

Example with Groq:

```bash
export LLM_BASE_URL=https://api.groq.com/openai/v1 LLM_API_KEY=gsk_... LLM_MODEL=llama-3.3-70b-versatile
uv run bibtex-assert tests/fixtures/probe_bad7.bib --mailto you@example.com
```

## Test fixture

`tests/fixtures/probe_bad7.bib` holds 14 entries: seven with a known error each, plus seven correct
controls.

| Key | What is wrong |
|---|---|
| `arefin2024unsupervised` | three invented co-authors, six real ones missing |
| `arjovsky2019invariant` | `Gulcevich` for `Gulrajani` |
| `augustin2023digin` | another paper's author list pasted in |
| `fel2022craft` | one author split into two fictitious people, three missing |
| `rottshaham2024maia` | `Herber` for `Rajaram` |
| `zhao2025textcam` | wrong first name, hidden behind `and others` (needs the LLM) |
| `zablocki2024gift` | broken accent macro for the first name, stray `and others` |

```bash
uv run pytest                 # offline unit tests (hand-verified records)
uv run pytest -m network      # live end-to-end run against the APIs
```

Result on the fixture (live APIs + `gpt-oss-120b` as judge, `examples/probe_bad7_report.md`): all seven bad
entries come back `HALLUCINATED` and all seven controls `PASS`. Rule-based only (`--no-llm`) catches the
five surname-level errors; the two first-name errors need the LLM.

## Verdict policy

Each entry gets a rule-based verdict and, when an LLM is configured, an LLM verdict. The reported verdict
is the **stricter** of the two, and the report says when they disagree. `@misc` entries with a URL (model
cards, dataset pages, blog posts) are checked by fetching the URL instead of searching for a paper.

## Limits

- The surname diff cannot see wrong first names. That is what the LLM step is for.
- Title search can miss papers with very short or very generic titles; the report says `hallucinated`
  when no record matches, so read the "best match" column before trusting that verdict.
- Free tiers change their limits without notice.

## Layout

```
src/bibtex_assertion/
  bib.py        BibTeX reader (no dependency)
  normalize.py  text and name normalization
  http.py       cached, paced, retrying HTTP
  sources/      arxiv, openalex, crossref, dblp -> Candidate
  lookup.py     gather candidates across sources
  compare.py    rule-based assessment
  judge.py      LLM adjudication (OpenAI-compatible)
  report.py     Markdown and JSON output
  cli.py        bibtex-assert entry point
```
