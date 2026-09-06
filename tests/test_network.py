"""Live end-to-end check on the seven known-bad entries. Run with: uv run pytest -m network"""

import pytest

from bibtex_assertion.cli import main

pytestmark = pytest.mark.network

BAD = ["arefin2024unsupervised", "arjovsky2019invariant", "augustin2023digin", "fel2022craft", "rottshaham2024maia"]


def test_live_rule_based_catches_the_surname_errors(tmp_path):
    out = tmp_path / "r.json"
    code = main(["tests/fixtures/probe_bad7.bib", "--no-llm", "--only", *BAD, "--json", str(out), "--md", str(tmp_path / "r.md")])
    assert code == 1
    assert out.read_text().count('"verdict": "hallucinated"') >= 5
