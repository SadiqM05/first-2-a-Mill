"""Retrieval checks against the REAL catalog and document index using tests/eval_questions.json.

- expected_catalog: catalog id that must rank first among catalog hits, or null for no catalog hit.
- expected_evidence: document evidence ids; at least one must be retrieved (checked only
  when the local index has been built with `python -m scripts.build_index`).
Live answer quality (expected_status) is checked by `python -m scripts.run_eval`, not here.
"""

import json

import pytest

from conftest import PROJECT_ROOT
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_INDEX_PATH
from reslink.ingest import load_index
from reslink.retrieval import KeywordRetriever

CASES = json.loads((PROJECT_ROOT / "tests" / "eval_questions.json").read_text(encoding="utf-8"))
CATALOG = load_catalog(DEFAULT_CATALOG_PATH)
CHUNKS, _ = load_index(DEFAULT_INDEX_PATH, CATALOG)
RETRIEVER = KeywordRetriever(CATALOG, CHUNKS)


def test_expected_ids_exist_in_catalog():
    ids = {r.id for r in CATALOG}
    referenced = {c["expected_catalog"] for c in CASES if c["expected_catalog"]}
    referenced |= {e.split("@")[0] for c in CASES for e in c.get("expected_evidence", [])}
    assert not referenced - ids, f"eval file references unknown ids: {referenced - ids}"


def test_expected_statuses_are_valid():
    assert {c["expected_status"] for c in CASES} <= {"grounded", "insufficient_evidence"}


@pytest.mark.parametrize("case", CASES, ids=[c["question"][:40] for c in CASES])
def test_catalog_retrieval(case):
    hits = RETRIEVER.retrieve_catalog(case["question"])
    if case["expected_catalog"] is None:
        assert hits == [], f"expected no catalog match, got {[h.resource.id for h in hits]}"
    else:
        assert hits, "expected a catalog match, got none"
        assert hits[0].resource.id == case["expected_catalog"]


DOC_CASES = [c for c in CASES if c.get("expected_evidence")]


@pytest.mark.skipif(not CHUNKS, reason="document index not built (python -m scripts.build_index)")
@pytest.mark.parametrize("case", DOC_CASES, ids=[c["question"][:40] for c in DOC_CASES])
def test_document_retrieval(case):
    got = {e.evidence_id for e in RETRIEVER.retrieve_documents(case["question"])}
    assert got & set(case["expected_evidence"]), f"expected one of {case['expected_evidence']}, got {got}"


def test_generic_resident_question_does_not_pull_roster():
    ids = [h.resource.id for h in RETRIEVER.retrieve_catalog("A resident needs something repaired. Where do I start?")]
    assert ids == ["maintenance-request-portal"]


def test_weekly_report_does_not_match_incident_form():
    # "report" appears in both the incident form title and the Reporting category;
    # it must not be double-counted into a false match.
    assert RETRIEVER.retrieve_catalog("Where do I submit my weekly RA report?") == []
