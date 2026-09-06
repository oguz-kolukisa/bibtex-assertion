"""Rule-based comparator against hand-verified records for the seven known-bad entries."""

from bibtex_assertion.compare import assess
from bibtex_assertion.sources import Candidate

REAL = {
    "arefin2024unsupervised": ("Unsupervised Concept Discovery Mitigates Spurious Correlations",
        ("Md Rifat Arefin", "Yan Zhang", "Aristide Baratin", "Francesco Locatello", "Irina Rish", "Dianbo Liu", "Kenji Kawaguchi"), "2024"),
    "arjovsky2019invariant": ("Invariant Risk Minimization",
        ("Martin Arjovsky", "Léon Bottou", "Ishaan Gulrajani", "David Lopez-Paz"), "2019"),
    "augustin2023digin": ("DiG-IN: Diffusion Guidance for Investigating Networks - Uncovering Classifier Differences, Neuron Visualisations, and Visual Counterfactual Explanations",
        ("Maximilian Augustin", "Yannic Neuhaus", "Matthias Hein"), "2024"),
    "fel2022craft": ("CRAFT: Concept Recursive Activation FacTorization for Explainability",
        ("Thomas Fel", "Agustin Picard", "Louis Bethune", "Thibaut Boissin", "David Vigouroux", "Julien Colin", "Rémi Cadène", "Thomas Serre"), "2023"),
    "rottshaham2024maia": ("A Multimodal Automated Interpretability Agent",
        ("Tamar Rott Shaham", "Sarah Schwettmann", "Franklin Wang", "Achyuta Rajaram", "Evan Hernandez", "Jacob Andreas", "Antonio Torralba"), "2024"),
    "zhao2025textcam": ("TextCAM: Explaining Class Activation Map with Text",
        ("Qiming Zhao", "Xingjian Li", "Xiaoyu Cao", "Xiaolong Wu", "Min Xu"), "2025"),
    "zablocki2024gift": ("GIFT: A Framework Towards Global Interpretable Faithful Textual Explanations of Vision Classifiers",
        ("Éloi Zablocki", "Valentin Gerard", "Amaia Cardiel", "Eric Gaussier", "Matthieu Cord", "Eduardo Valle"), "2024"),
    "he2016deep": ("Deep Residual Learning for Image Recognition",
        ("Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"), "2016"),
    "geirhos2020shortcut": ("Shortcut learning in deep neural networks",
        ("Robert Geirhos", "Jörn-Henrik Jacobsen", "Claudio Michaelis", "Richard Zemel", "Wieland Brendel", "Matthias Bethge", "Felix A. Wichmann"), "2020"),
}


def record(key):
    title, authors, year = REAL[key]
    return [Candidate("arxiv", title, authors, year=year)]


def verdict(entries, key):
    return assess(entries[key], record(key))


def test_invented_authors_are_hallucinated(bad7_entries):
    out = verdict(bad7_entries, "arefin2024unsupervised")
    assert out.verdict == "hallucinated"
    assert set(out.invented_authors) == {"bhatt", "cardoso cachopo", "kim"}


def test_copied_author_list_is_hallucinated(bad7_entries):
    out = verdict(bad7_entries, "augustin2023digin")
    assert out.verdict == "hallucinated"
    assert set(out.invented_authors) == {"boreiko", "croce"}


def test_split_and_invented_names_in_craft(bad7_entries):
    out = verdict(bad7_entries, "fel2022craft")
    assert out.verdict == "hallucinated"
    assert "music" in out.invented_authors and "boutin" in out.invented_authors


def test_single_wrong_surname_is_hallucinated(bad7_entries):
    assert verdict(bad7_entries, "arjovsky2019invariant").invented_authors == ["gulcevich"]
    assert verdict(bad7_entries, "rottshaham2024maia").invented_authors == ["herber"]


def test_wrong_first_name_hidden_by_et_al_is_not_caught_by_surnames(bad7_entries):
    out = verdict(bad7_entries, "zhao2025textcam")
    assert out.verdict == "ok"  # surname 'zhao' matches; the LLM judge is needed for first names


def test_gift_missing_accent_is_minor_at_most(bad7_entries):
    out = verdict(bad7_entries, "zablocki2024gift")
    assert out.verdict in {"ok", "minor"}
    assert not out.invented_authors


def test_correct_entries_pass(bad7_entries):
    assert verdict(bad7_entries, "he2016deep").verdict == "ok"
    assert verdict(bad7_entries, "geirhos2020shortcut").verdict == "ok"


def test_no_matching_title_is_hallucinated(bad7_entries):
    out = assess(bad7_entries["he2016deep"], [Candidate("dblp", "Something Else Entirely", ("A B",))])
    assert out.verdict == "hallucinated"


def test_artifact_without_record_is_unverifiable(bad7_entries):
    assert assess(bad7_entries["flux-2-2025"], []).verdict == "unverifiable"


def test_dataset_page_with_loose_record_is_unverifiable(bad7_entries):
    loose = [Candidate("crossref", "ImageNet dataset", ("A Toumpanakis", "B Liao"), year="2021")]
    assert assess(bad7_entries["angn_imagenet100"], loose).verdict == "unverifiable"


def test_compound_surname_is_not_a_misspelling(bad7_entries):
    out = verdict(bad7_entries, "rottshaham2024maia")
    assert out.misspelled_authors == [] and out.invented_authors == ["herber"]
