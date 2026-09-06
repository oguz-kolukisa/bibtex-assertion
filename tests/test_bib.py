from bibtex_assertion.bib import parse_bib, split_authors, has_et_al


def test_parses_all_fixture_entries(bad7_entries):
    assert len(bad7_entries) == 14
    assert "arjovsky2019invariant" in bad7_entries


def test_fields_and_properties(bad7_entries):
    entry = bad7_entries["arjovsky2019invariant"]
    assert entry.entry_type == "misc"
    assert entry.title == "Invariant Risk Minimization"
    assert entry.year == "2019"
    assert entry.arxiv_id == "1907.02893"
    assert entry.authors == ["Arjovsky, Martin", "Bottou, Leon", "Gulcevich, Ishaan", "Lopez-Paz, David"]


def test_skips_string_macros():
    text = '@STRING{cvpr = {CVPR}}\n@article{k, title={T}, author={A B}, year={2020}}'
    entries = parse_bib(text)
    assert [e.key for e in entries] == ["k"]


def test_nested_braces_in_title():
    entries = parse_bib('@article{k, title={{DiG-IN}: Diffusion {Guidance} for Nets}, author={A B}}')
    assert entries[0].title == "DiG-IN: Diffusion Guidance for Nets"


def test_split_authors_drops_others():
    assert split_authors("Kim, Been and Wattenberg, Martin and others") == ["Kim, Been", "Wattenberg, Martin"]
    assert has_et_al("Zhao, Zhicheng and others")
