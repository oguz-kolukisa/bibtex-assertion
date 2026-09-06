from bibtex_assertion.compare import assess
from bibtex_assertion.fix import bibtex_name, fixed_bib
from bibtex_assertion.report import Result
from bibtex_assertion.sources import Candidate
from bibtex_assertion.normalize import surname


def test_bibtex_name_forms():
    assert bibtex_name("Ishaan Gulrajani") == "Gulrajani, Ishaan"
    assert bibtex_name("Tamar Rott Shaham") == "Shaham, Tamar Rott"
    assert bibtex_name("Arjovsky, Martin") == "Arjovsky, Martin"


def test_dblp_suffix_and_compound_surnames():
    assert surname("Xiao Wang 0038") == "wang"
    entry_side, record_side = "del ser", "ser"
    from bibtex_assertion.compare import _is_substring
    assert _is_substring(entry_side, record_side)


def test_fixed_bib_rewrites_only_author_problems(bad7_entries):
    entry = bad7_entries["arjovsky2019invariant"]
    real = Candidate("arxiv", entry.title, ("Martin Arjovsky", "Léon Bottou", "Ishaan Gulrajani", "David Lopez-Paz"), year="2019")
    text, keys = fixed_bib([Result(assess(entry, [real]), entry=entry)])
    assert keys == ["arjovsky2019invariant"]
    assert "author = {Arjovsky, Martin and Bottou, Léon and Gulrajani, Ishaan and Lopez-Paz, David}" in text
    assert "eprint = {1907.02893}" in text


def test_fixed_bib_skips_correct_entries(bad7_entries):
    entry = bad7_entries["he2016deep"]
    real = Candidate("arxiv", entry.title, ("Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"), year="2016")
    assert fixed_bib([Result(assess(entry, [real]), entry=entry)]) == ("", [])


def test_author_field_normalizes_lookalike_unicode(bad7_entries):
    entry = bad7_entries["he2016deep"]
    rec = Candidate("openalex", entry.title, ("Chun‐Hao Chang", "Κonstantinos Thomas", "Xiangyu Zhang", "Shaoqing Ren"), year="2016")
    result = Result(assess(entry, [rec]), entry=entry)
    result.rules.invented_authors.append("forced")  # make it fixable for the test
    from bibtex_assertion.fix import fixed_author_field
    field = fixed_author_field(result)
    assert "Chun-Hao" in field and "Konstantinos" in field
