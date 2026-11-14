"""Retrieval checks against the REAL catalog, chunk index and Chroma index (tests/eval_questions.json).

Keyword retriever (always runs):
- expected_catalog: catalog id that must rank first among keyword catalog hits, or null for none.
- expected_evidence: at least one must be among keyword document pages.
- Cases marked "paraphrase" are skipped: keyword search is known not to handle them.

Hybrid retriever (skipped unless `python -m scripts.build_index` has built the semantic index):
- every supported case (paraphrases included) must have a target in the top 3 catalog
  hits or top 3 pages, except documented known misses.
Live answer quality is checked by `python -m scripts.run_eval`, not here.
"""

import json
import re

import pytest

from conftest import PROJECT_ROOT
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_CHROMA_PATH, DEFAULT_INDEX_PATH, PROJECT_ROOT
from reslink.ingest import load_chunks
from reslink.retrieval import HybridRetriever, KeywordRetriever
from reslink.semantic import CATALOG_MAX_DISTANCE, DEFAULT_MAX_DISTANCE, SemanticIndex

ALL_CASES = json.loads((PROJECT_ROOT / "tests" / "eval_questions.json").read_text(encoding="utf-8"))
# Follow-up questions only make sense with their conversation; they're covered by
# tests/test_response_quality.py (history-aware retrieval), not by standalone retrieval here.
CASES = [c for c in ALL_CASES if not c.get("follow_up_of")]
CATALOG = load_catalog(DEFAULT_CATALOG_PATH)
CHUNKS, _ = load_chunks(DEFAULT_INDEX_PATH, CATALOG, PROJECT_ROOT)
RETRIEVER = KeywordRetriever(CATALOG, CHUNKS)
SEMANTIC, SEMANTIC_STATUS = SemanticIndex.open(DEFAULT_CHROMA_PATH, CATALOG, CHUNKS)
needs_semantic = pytest.mark.skipif(SEMANTIC is None, reason=f"semantic index unavailable: {SEMANTIC_STATUS}")

# Supported questions hybrid retrieval still misses (documented in docs/EVALUATION.md).
KNOWN_KEYWORD_MISSES = {"What is SC Logic?", "How do I return a letter to sender?"}  # hybrid finds the latter
KNOWN_HYBRID_MISSES = {"My resident can't get into their room", "What is SC Logic?"}


def _id(case):
    return case["question"][:40]


def targets(case) -> set[str]:
    out = set(case.get("expected_evidence", []))
    if case.get("expected_catalog"):
        out.add(case["expected_catalog"])
    return out


def test_expected_ids_exist_in_catalog():
    ids = {r.id for r in CATALOG}
    referenced = {re.split(r"[@#]", t)[0] for c in CASES for t in targets(c)}
    assert not referenced - ids, f"eval file references unknown ids: {referenced - ids}"


def test_expected_statuses_are_valid():
    assert {c["expected_status"] for c in CASES} <= {"grounded", "insufficient_evidence"}


def test_live_subset_is_small():
    # Gemini quota budget; privacy-blocked questions make no API call.
    for tag in ("live", "live_m6"):
        assert sum(1 for c in ALL_CASES if c.get(tag) and not c.get("privacy")) <= 8, tag


def test_follow_up_cases_reference_an_earlier_question():
    asked = []
    for c in ALL_CASES:
        if c.get("follow_up_of"):
            assert c["follow_up_of"] in asked, c["question"]
        asked.append(c["question"])


# Procedure questions are checked by document targets (below), not by catalog-null expectations.
KEYWORD_CASES = [c for c in CASES if not c.get("paraphrase") and not c.get("procedure")]
KEYWORD_DOC_CASES = [c for c in CASES if not c.get("paraphrase") and c.get("expected_evidence")]


@pytest.mark.parametrize("case", KEYWORD_CASES, ids=_id)
def test_keyword_catalog_retrieval(case):
    hits = [h for h in RETRIEVER.retrieve_catalog(case["question"])
            if h.resource.id not in case.get("acceptable_catalog", [])]
    if not case.get("expected_catalog"):
        assert hits == [], f"expected no catalog match, got {[h.resource.id for h in hits]}"
    else:
        assert hits, "expected a catalog match, got none"
        assert hits[0].resource.id == case["expected_catalog"]


DOC_CASES = KEYWORD_DOC_CASES


@pytest.mark.skipif(not CHUNKS, reason="document index not built (python -m scripts.build_index)")
@pytest.mark.parametrize("case", DOC_CASES, ids=_id)
def test_keyword_document_retrieval(case):
    if case["question"] in KNOWN_KEYWORD_MISSES:
        pytest.xfail("documented known keyword miss")
    got = {e.evidence_id for e in RETRIEVER.retrieve_documents(case["question"])}
    assert got & set(case["expected_evidence"]), f"expected one of {case['expected_evidence']}, got {got}"


def test_generic_resident_question_does_not_pull_roster():
    ids = [h.resource.id for h in RETRIEVER.retrieve_catalog("A resident needs something repaired. Where do I start?")]
    assert ids == ["maintenance-request-portal"]


def test_weekly_report_does_not_match_incident_form():
    # "report" appears in both the incident form title and the Reporting category;
    # it must not be double-counted into a false match.
    assert RETRIEVER.retrieve_catalog("Where do I submit my weekly RA report?") == []


# --- hybrid -------------------------------------------------------------------------------

SUPPORTED = [c for c in CASES if targets(c)]


def _hybrid():
    return HybridRetriever(RETRIEVER, SEMANTIC, max_distance=DEFAULT_MAX_DISTANCE,
                           catalog_max_distance=CATALOG_MAX_DISTANCE)


@needs_semantic
@pytest.mark.parametrize("case", SUPPORTED, ids=_id)
def test_hybrid_finds_target_in_top3(case):
    evidence = _hybrid().retrieve(case["question"])
    catalog = [e.evidence_id for e in evidence if e.source == "catalog"][:3]
    docs = [e.evidence_id for e in evidence if e.source == "document"][:3]
    found = bool(set(catalog + docs) & targets(case))
    if case["question"] in KNOWN_HYBRID_MISSES:
        pytest.xfail("documented known miss")
    assert found, f"targets {targets(case)} not in catalog {catalog} / pages {docs}"


@needs_semantic
@pytest.mark.parametrize("case", [c for c in SUPPORTED if not c.get("paraphrase")], ids=_id)
def test_hybrid_never_loses_a_keyword_hit(case):
    """No regression: whatever keyword retrieval found in its top 3, hybrid still has in top 3."""
    kw = RETRIEVER.retrieve(case["question"])
    hy = _hybrid().retrieve(case["question"])
    kw_found = {e.evidence_id for e in kw} & targets(case)
    hy_ids = {e.evidence_id for e in hy if e.source == "catalog"} | {
        e.evidence_id for e in [x for x in hy if x.source == "document"][:3]
    }
    assert kw_found <= hy_ids, f"hybrid dropped {kw_found - hy_ids}"


@needs_semantic
def test_hybrid_evidence_only_references_catalog_resources():
    ids = {r.id for r in CATALOG}
    for case in CASES:
        for e in _hybrid().retrieve(case["question"]):
            assert e.resource.id in ids
            assert (e.source == "document") == (e.page is not None)
            assert e.resource.content_type != "portal" or e.source == "catalog"  # portals: metadata only
