"""The hallucinated-reference criteria used by ICLR, ICML and NeurIPS 2026 program chairs."""

CRITERIA = """\
1. If no document with a title anywhere near the cited title can be found, the reference is HALLUCINATED.
   Minor title differences are not evidence of hallucination.
2. If the author list is only slightly wrong (a few subtle misspellings, a few missing authors, or wrong
   order), the reference is NOT hallucinated but must be flagged as MINOR for the authors to fix.
3. If the author list has added people who are not authors of the publication, or is missing a large
   fraction of the authors, the reference is HALLUCINATED.
4. If the venue is a real venue but wrong for this reference (wrong journal, wrong conference, wrong arXiv
   id, wrong year), the reference is NOT hallucinated but must be flagged as MINOR.
5. If there is no evidence that the venue exists, the reference is HALLUCINATED.
6. Generic references to existing artifacts without a document (a model card, a dataset page, a blog post)
   are fine when the artifact exists.
"""
