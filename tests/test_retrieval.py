import pytest

from reslink.catalog import load_catalog, parse_catalog
from reslink.retrieval import KeywordRetriever, evidence_text, tokenize


@pytest.fixture
def resources(placeholder_catalog_path):
    return load_catalog(placeholder_catalog_path, allow_placeholders=True)


def test_tokenize_drops_stopwords_and_stems():
    assert tokenize("Where do I find the repairs?") == ["find", "repair"]
    assert tokenize("Repairing REPAIRED repair") == ["repair", "repair", "repair"]
    assert tokenize("the a to") == []


def test_keyword_match_ranks_expected_resource_first(resources):
    hits = KeywordRetriever(resources).retrieve("Something is broken and needs repair")
    assert hits[0].resource.id == "placeholder-maintenance-001"
    assert hits[0].score >= 2.0


def test_no_match_returns_empty(resources):
    assert KeywordRetriever(resources).retrieve("parking permit for visitors") == []


def test_stopword_only_query_returns_empty(resources):
    assert KeywordRetriever(resources).retrieve("where do I do it?") == []


def test_top_k_limits_results(resources):
    hits = KeywordRetriever(resources, min_score=0.5).retrieve("reporting resource", top_k=1)
    assert len(hits) == 1


def test_phrase_keyword_needs_whole_phrase():
    [r] = parse_catalog(
        [{"id": "x", "title": "T", "category": "maintenance", "url": "https://example.org/x",
          "keywords": ["locked out"]}],
        allow_placeholders=True,
    )
    retriever = KeywordRetriever([r])
    assert retriever.score("I got locked out", r) == 3.0
    assert retriever.score("the door is locked", r) == 0.0


def test_evidence_text_never_contains_url(resources):
    for r in resources:
        assert r.url not in evidence_text(r)
        assert "http" not in evidence_text(r)


def test_empty_catalog_retrieves_nothing():
    assert KeywordRetriever([]).retrieve("repair") == []


# --- document chunks ----------------------------------------------------------

from reslink.models import Chunk  # noqa: E402

PDF_ID = "placeholder-reporting-001"


@pytest.fixture
def doc_retriever(resources):
    chunks = [
        Chunk(PDF_ID, 1, 0, "PLACEHOLDER text: staff must hold three open door hours each week in the hall"),
        Chunk(PDF_ID, 1, 1, "PLACEHOLDER text: open door hours overlap chunk for the hall staff"),
        Chunk(PDF_ID, 2, 0, "PLACEHOLDER text: minimum GPA requirement for hall staff"),
        Chunk(PDF_ID, 3, 0, "PLACEHOLDER text: hall staff meetings are held in the hall"),
        Chunk("not-in-catalog", 1, 0, "open door hours orphan"),
    ]
    return KeywordRetriever(resources, chunks)


def test_document_hit_has_page_and_evidence_id(doc_retriever):
    [hit] = doc_retriever.retrieve_documents("what is the minimum GPA?")
    assert hit.source == "document" and hit.page == 2
    assert hit.evidence_id == f"{PDF_ID}@p2"
    assert hit.text.startswith("Source: ") and "page 2" in hit.text


def test_one_evidence_per_page(doc_retriever):
    hits = doc_retriever.retrieve_documents("open door hours")
    pages = [h.page for h in hits]
    assert pages[0] == 1 and len(pages) == len(set(pages))


def test_chunks_not_in_catalog_are_ignored(doc_retriever):
    assert all(h.resource.id == PDF_ID for h in doc_retriever.retrieve_documents("open door hours orphan"))


def test_common_words_weigh_less_than_rare_words(doc_retriever):
    # "hall"/"staff" appear in every chunk; "gpa" in one. IDF must reflect that.
    assert doc_retriever._idf["hall"] < doc_retriever._idf["gpa"]
    assert doc_retriever._idf["staff"] < doc_retriever._idf["gpa"]


def test_longer_query_needs_two_matching_words(doc_retriever):
    assert doc_retriever.retrieve_documents("what about the GPA of my roommate's cat") == []


def test_retrieve_combines_catalog_first(resources, doc_retriever):
    hits = doc_retriever.retrieve("broken repair minimum GPA")
    assert hits[0].source == "catalog"
    assert any(h.source == "document" for h in hits)


def test_all_matching_chunks_of_a_page_are_merged(doc_retriever):
    [hit] = [h for h in doc_retriever.retrieve_documents("open door hours") if h.page == 1]
    assert "three open door hours" in hit.text  # chunk 0
    assert "overlap chunk" in hit.text  # chunk 1 (lower-scoring) is not dropped
