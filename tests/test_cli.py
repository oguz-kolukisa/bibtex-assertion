from unittest.mock import patch

from bibtex_assertion import cli
from bibtex_assertion.compare import Assessment
from bibtex_assertion.report import Result


def test_reports_are_rewritten_after_each_entry(tmp_path, bad7_entries):
    md, js = tmp_path / "r.md", tmp_path / "r.json"
    seen = []

    def fake_check(entry, lookup, judge):
        seen.append(js.exists() and js.read_text().count('"key"'))
        return Result(Assessment(entry.key, "ok"), entry=entry)

    args = cli._parse_args(["x.bib", "--no-llm", "--cache", "", "--md", str(md), "--json", str(js)])
    with patch.object(cli, "_check_one", side_effect=fake_check):
        cli.run(list(bad7_entries.values())[:3], args)
    assert seen == [False, 1, 2] and js.read_text().count('"key"') == 3 and "Entries checked: **3**" in md.read_text()
