from bibtex_assertion.compare import Assessment
from bibtex_assertion.report import Result, to_markdown, to_json


def test_llm_verdict_overrides_rules_and_flags_disagreement():
    result = Result(Assessment("k", "ok"), {"verdict": "hallucinated", "explanation": "first name wrong"})
    assert result.verdict == "hallucinated" and result.disagreement
    md = to_markdown([result])
    assert "HALLUCINATED: 1" in md and "rules said ok" in md


def test_json_roundtrip_has_keys():
    payload = to_json([Result(Assessment("k", "minor", problems=["year 2019 vs 2020"]))])
    assert '"verdict": "minor"' in payload and "year 2019 vs 2020" in payload


def test_verdict_takes_the_stricter_side():
    strict_rules = Result(Assessment("k", "hallucinated"), {"verdict": "minor"})
    strict_llm = Result(Assessment("k", "ok"), {"verdict": "hallucinated"})
    assert strict_rules.verdict == "hallucinated" and strict_llm.verdict == "hallucinated"
    assert Result(Assessment("k", "unverifiable"), {"verdict": "ok"}).verdict == "unverifiable"
