"""Semantic index tests: what gets embedded, fingerprints, telemetry, and real Chroma build/open.

The real-Chroma tests use a temporary directory and skip if chromadb or the cached ONNX
model is unavailable (no network access is ever triggered by the test suite).
"""

import pytest

from reslink.catalog import load_catalog
from reslink.models import Chunk
from reslink.semantic import (
    COLLECTION_NAME,
    SemanticIndex,
    build_documents,
    catalog_text,
    fingerprint,
    model_is_cached,
)

PDF_ID = "placeholder-reporting-001"
PORTALISH_ID = "placeholder-maintenance-001"  # a non-pdf resource

needs_model = pytest.mark.skipif(not model_is_cached(), reason="ONNX model not cached (run build_index once)")


@pytest.fixture
def resources(placeholder_catalog_path):
    return load_catalog(placeholder_catalog_path, allow_placeholders=True)


@pytest.fixture
def chunks():
    return [
        Chunk(PDF_ID, 1, 0, "PLACEHOLDER text: animals are not permitted in the halls"),
        Chunk(PDF_ID, 2, 0, "PLACEHOLDER text: the monthly salary for this position"),
        Chunk(PORTALISH_ID, 1, 0, "PLACEHOLDER text that must never be indexed"),
        Chunk("not-in-catalog", 1, 0, "orphan text"),
    ]


def test_build_documents_contents(resources, chunks):
    docs = build_documents(resources, chunks)
    ids = [d.id for d in docs]
    assert [i for i in ids if i.startswith("catalog:")] == [f"catalog:{r.id}" for r in resources]
    assert [i for i in ids if i.startswith("doc:")] == [f"doc:{PDF_ID}@p1#c0", f"doc:{PDF_ID}@p2#c0"]
    # non-pdf resources and orphans contribute no document text
    assert not any("must never be indexed" in d.text or "orphan" in d.text for d in docs)
    meta = next(d.metadata for d in docs if d.id == f"doc:{PDF_ID}@p2#c0")
    assert meta == {"kind": "document", "resource_id": PDF_ID, "page": 2, "chunk_index": 0}


def test_catalog_text_is_metadata_without_urls(resources):
    for r in resources:
        text = catalog_text(r)
        assert r.title in text and r.url not in text and "http" not in text


def test_fingerprint_changes_with_content(resources, chunks):
    base = fingerprint(build_documents(resources, chunks))
    assert base == fingerprint(build_documents(resources, list(reversed(chunks))))  # order-independent
    changed = chunks[:1] + [Chunk(PDF_ID, 2, 0, "PLACEHOLDER text: different salary text")]
    assert base != fingerprint(build_documents(resources, changed))
    assert base != fingerprint(build_documents(resources[:-1], chunks))


def test_open_reports_missing_index(tmp_path, resources, chunks):
    index, status = SemanticIndex.open(tmp_path / "nope", resources, chunks)
    assert index is None and "not built" in status


def test_telemetry_disabled_in_process():
    import os

    import reslink.semantic  # noqa: F401

    assert os.environ.get("ANONYMIZED_TELEMETRY") == "False"


@needs_model
def test_build_open_search_roundtrip(tmp_path, resources, chunks):
    path = tmp_path / "chroma"
    SemanticIndex.build(path, resources, chunks)
    index, status = SemanticIndex.open(path, resources, chunks)
    assert status == "ready"
    hits = index.search("can I keep a pet in my room", n=3, max_distance=2.0, kind="document")
    assert hits[0].resource_id == PDF_ID and hits[0].page == 1 and hits[0].chunk_index == 0
    assert all(h.kind == "document" for h in hits)
    cat_hits = index.search("can I keep a pet", n=5, max_distance=2.0, kind="catalog")
    assert {h.kind for h in cat_hits} == {"catalog"} and all(h.page is None for h in cat_hits)
    assert index.search("anything", n=5, max_distance=0.0) == []  # threshold applies


@needs_model
def test_open_detects_stale_index(tmp_path, resources, chunks):
    path = tmp_path / "chroma"
    SemanticIndex.build(path, resources, chunks)
    edited = chunks[:1] + [Chunk(PDF_ID, 2, 0, "PLACEHOLDER text: edited content")]
    index, status = SemanticIndex.open(path, resources, edited)
    assert index is None and "stale" in status


@needs_model
def test_rebuild_replaces_collection(tmp_path, resources, chunks):
    path = tmp_path / "chroma"
    SemanticIndex.build(path, resources, chunks)
    SemanticIndex.build(path, resources, chunks[:1])
    index, status = SemanticIndex.open(path, resources, chunks[:1])
    assert status == "ready"
    assert index._collection.count() == len(build_documents(resources, chunks[:1]))
    assert index._collection.name == COLLECTION_NAME
