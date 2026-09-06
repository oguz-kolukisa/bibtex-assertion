from pathlib import Path

import pytest

from bibtex_assertion.bib import parse_bib

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def bad7_entries():
    return {e.key: e for e in parse_bib((FIXTURES / "probe_bad7.bib").read_text(encoding="utf-8"))}
