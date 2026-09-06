from bibtex_assertion.artifact import artifact_url, assess_artifact


def test_artifact_url_found_in_howpublished(bad7_entries):
    assert artifact_url(bad7_entries["flux-2-2025"]).startswith("https://bfl.ai/")
    assert artifact_url(bad7_entries["angn_imagenet100"]).startswith("https://www.kaggle.com/")
    assert artifact_url(bad7_entries["he2016deep"]) == ""


def test_assess_artifact_by_resolution(bad7_entries):
    entry = bad7_entries["flux-2-2025"]
    assert assess_artifact(entry, True).verdict == "ok"
    assert assess_artifact(entry, False).verdict == "unverifiable"
