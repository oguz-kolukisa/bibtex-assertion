from bibtex_assertion.compare import assess
from bibtex_assertion.judge import build_prompt, parse_json
from bibtex_assertion.sources import Candidate


def test_prompt_contains_entry_records_and_criteria(bad7_entries):
    entry = bad7_entries["zhao2025textcam"]
    cands = [Candidate("arxiv", entry.title, ("Qiming Zhao", "Xingjian Li"), year="2025")]
    prompt = build_prompt(entry, cands, assess(entry, cands))
    assert "HALLUCINATED" in prompt and "Qiming Zhao" in prompt and "zhao2025textcam" in prompt


def test_parse_json_tolerates_prose_wrapping():
    assert parse_json('Sure:\n{"verdict": "minor", "explanation": "x"}\n')["verdict"] == "minor"


def test_parse_json_handles_garbage():
    assert parse_json("no json here")["verdict"] == "unverifiable"


def test_llm_invented_claim_refuted_by_records_is_dropped():
    from bibtex_assertion.judge import validate_against_records
    cands = [Candidate("arxiv", "Qwen2.5-VL Technical Report", ("Shuai Bai", "Mingkun Yang"), year="2025")]
    verdict = validate_against_records({"verdict": "hallucinated", "invented_authors": ["Mingkun Yang"], "explanation": "x"}, cands)
    assert verdict["verdict"] == "minor" and verdict["invented_authors"] == []
    kept = validate_against_records({"verdict": "hallucinated", "invented_authors": ["Zhicheng Zhao"], "explanation": "x"}, cands)
    assert kept["verdict"] == "hallucinated"
