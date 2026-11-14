"""Hybrid retrieval unit tests with a fake semantic index (deterministic, no model, offline)."""

import pytest

from reslink.catalog import load_catalog
from reslink.models import Chunk
from reslink.retrieval import HybridRetriever, KeywordRetriever, rrf_fuse
from reslink.semantic import SemanticHit

PDF_ID = "placeholder-reporting-001"  # content_type "pdf" in the fixture
MAINT_ID = "placeholder-maintenance-001"  # webpage


class FakeSemantic:
    """Returns canned hits per kind and records calls."""

    def __init__(self, catalog=(), documents=(), error: Exception | None = None):
        self.hits = {"catalog": list(catalog), "document": list(documents)}
        self.error = error
        self.calls = []

    def search(self, query, n=8, max_distance=1.0, kind=None):
        self.calls.append((query, kind, n, max_distance))
        if self.error:
            raise self.error
        return [h for h in self.hits[kind] if h.distance <= max_distance][:n]


def doc(page, chunk_index=0, distance=0.5, resource_id=PDF_ID):
    return SemanticHit("document", resource_id, distance, page=page, chunk_index=chunk_index)


def cat(resource_id, distance=0.5):
    return SemanticHit("catalog", resource_id, distance)


@pytest.fixture
def keyword(placeholder_catalog_path):
    resources = load_catalog(placeholder_catalog_path, allow_placeholders=True)
    chunks = [
        Chunk(PDF_ID, 1, 0, "PLACEHOLDER text: open door hours are held three evenings each week"),
        Chunk(PDF_ID, 2, 0, "PLACEHOLDER text: animals are not permitted except fish and service animals"),
        Chunk(PDF_ID, 3, 0, "PLACEHOLDER text: candle warmers and open flame are prohibited"),
        Chunk(PDF_ID, 3, 1, "PLACEHOLDER text: second chunk on page three about decorations"),
        Chunk(PDF_ID, 4, 0, "PLACEHOLDER text: remuneration is a monthly salary"),
    ]
    return KeywordRetriever(resources, chunks)


# --- RRF ------------------------------------------------------------------------------------


def test_rrf_rewards_agreement():
    fused = [item for item, _ in rrf_fuse([["a", "b", "c"], ["b", "d"]])]
    assert fused[0] == "b"  # found by both rankers
    assert set(fused) == {"a", "b", "c", "d"}


def test_rrf_is_deterministic_on_ties():
    assert [i for i, _ in rrf_fuse([["x"], ["y"]])] == ["x", "y"]
    assert [i for i, _ in rrf_fuse([["y"], ["x"]])] == ["y", "x"]


def test_rrf_empty():
    assert rrf_fuse([[], []]) == []


# --- fallback ---------------------------------------------------------------------------------


def test_no_semantic_is_identical_to_keyword(keyword):
    hybrid = HybridRetriever(keyword, None)
    for q in ["open door hours", "something broken needs repair", "nothing matches xyz"]:
        assert hybrid.retrieve(q) == keyword.retrieve(q)
    assert hybrid.last_mode == "keyword"


def test_semantic_error_falls_back_to_keyword(keyword):
    hybrid = HybridRetriever(keyword, FakeSemantic(error=RuntimeError("index corrupted")))
    assert hybrid.retrieve("open door hours") == keyword.retrieve("open door hours")
    assert hybrid.last_mode == "keyword (semantic error)"


def test_blank_query_skips_semantic(keyword):
    sem = FakeSemantic(documents=[doc(2)])
    assert HybridRetriever(keyword, sem).retrieve("   ") == []
    assert sem.calls == []


# --- semantic contribution --------------------------------------------------------------------


def test_paraphrase_found_only_by_semantic(keyword):
    # "pet" shares no words with the 'animals' page; semantic supplies it with page citation.
    assert keyword.retrieve("can I have a pet") == []
    hybrid = HybridRetriever(keyword, FakeSemantic(documents=[doc(2)]))
    [e] = hybrid.retrieve("can I have a pet")
    assert (e.source, e.evidence_id, e.page) == ("document", f"{PDF_ID}@p2", 2)
    assert "animals are not permitted" in e.text and e.text.startswith("Source: ")
    assert hybrid.last_mode == "hybrid"


def test_page_found_by_both_ranks_first(keyword):
    # keyword finds p1 ("open door hours"); semantic ranks p4 then p1 -> p1 found by both wins.
    hybrid = HybridRetriever(keyword, FakeSemantic(documents=[doc(4), doc(1)]))
    pages = [e.page for e in hybrid.retrieve("open door hours") if e.source == "document"]
    assert pages[0] == 1 and 4 in pages


def test_semantic_chunks_merge_into_page_evidence(keyword):
    hybrid = HybridRetriever(keyword, FakeSemantic(documents=[doc(3, 0), doc(3, 1)]))
    [e] = [x for x in hybrid.retrieve("is a lava lamp ok") if x.source == "document"]
    assert "candle warmers" in e.text and "second chunk" in e.text
    assert e.text.count("candle warmers") == 1  # deduplicated


def test_catalog_and_document_evidence_stay_distinct(keyword):
    hybrid = HybridRetriever(keyword, FakeSemantic(catalog=[cat(MAINT_ID)], documents=[doc(2)]))
    evidence = hybrid.retrieve("can I have a pet")
    assert [(e.source, e.evidence_id) for e in evidence] == [("catalog", MAINT_ID), ("document", f"{PDF_ID}@p2")]
    assert evidence[0].page is None and "http" not in evidence[0].text


def test_unknown_resources_and_stale_chunks_are_dropped(keyword):
    sem = FakeSemantic(
        catalog=[cat("not-in-catalog")],
        documents=[doc(2, resource_id="not-in-catalog"), doc(9), doc(2, chunk_index=7)],
    )
    assert HybridRetriever(keyword, sem).retrieve("can I have a pet") == []


def test_distance_limits_apply_per_kind(keyword):
    sem = FakeSemantic(catalog=[cat(MAINT_ID, 0.7)], documents=[doc(2, distance=0.7)])
    hybrid = HybridRetriever(keyword, sem, max_distance=0.75, catalog_max_distance=0.65)
    evidence = hybrid.retrieve("can I have a pet")
    assert [e.source for e in evidence] == ["document"]  # catalog hit at 0.70 > 0.65
    assert {(k, d) for _, k, _, d in sem.calls} == {("catalog", 0.65), ("document", 0.75)}


def test_result_size_limits(keyword):
    sem = FakeSemantic(catalog=[cat(MAINT_ID), cat(PDF_ID)], documents=[doc(1), doc(2), doc(3), doc(4)])
    evidence = HybridRetriever(keyword, sem).retrieve("open door hours")  # defaults
    assert sum(e.source == "catalog" for e in evidence) <= 3
    docs = [e for e in evidence if e.source == "document"]
    assert len(docs) <= 3 and len({e.page for e in docs}) == len(docs)


def test_semantic_catalog_contributes_at_most_one_by_default(keyword):
    sem = FakeSemantic(catalog=[cat(MAINT_ID), cat(PDF_ID)])
    evidence = HybridRetriever(keyword, sem).retrieve("zzz unrelated words")
    assert [e.evidence_id for e in evidence] == [MAINT_ID]
