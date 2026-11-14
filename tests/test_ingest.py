import json

import pytest

from reslink.catalog import load_catalog
from reslink.ingest import chunk_pages, chunk_text, extract_pdf_pages, load_index, normalize_text, save_index
from reslink.models import Chunk


@pytest.fixture
def resources(placeholder_catalog_path):
    return load_catalog(placeholder_catalog_path, allow_placeholders=True)


def test_normalize_text_collapses_whitespace_and_quotes():
    assert normalize_text("the ― 5 P’s\n\n  and more") == "the \" 5 P's and more"


def test_chunk_text_windows_with_overlap():
    words = " ".join(f"w{i}" for i in range(300))
    chunks = chunk_text(words, chunk_words=100, overlap=20)
    assert [len(c.split()) for c in chunks] == [100, 100, 100, 60]
    assert chunks[1].split()[0] == "w80"  # 20-word overlap


def test_chunk_text_short_and_empty():
    assert chunk_text("just a few words here") == ["just a few words here"]
    assert chunk_text("   ") == []


def test_chunk_text_drops_tiny_tail():
    words = " ".join(f"w{i}" for i in range(83))
    chunks = chunk_text(words, chunk_words=80, overlap=0)
    assert len(chunks) == 1  # 3-word tail is below MIN_CHUNK_WORDS


def test_chunk_text_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_words=10, overlap=10)


def test_chunk_pages_keeps_page_numbers():
    chunks = chunk_pages("doc", [(1, "alpha beta"), (3, "gamma delta")])
    assert [(c.page, c.chunk_index, c.text) for c in chunks] == [(1, 0, "alpha beta"), (3, 0, "gamma delta")]


def test_extract_pdf_pages_roundtrip(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    path = tmp_path / "t.pdf"
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "PLACEHOLDER page one")
    doc.new_page()  # blank page is skipped
    doc.new_page().insert_text((72, 72), "PLACEHOLDER page three")
    doc.save(path)
    pages = extract_pdf_pages(path)
    assert [n for n, _ in pages] == [1, 3]
    assert "page three" in pages[1][1]


def test_index_roundtrip(tmp_path, resources):
    path = tmp_path / "index" / "chunks.json"
    chunks = [Chunk("placeholder-reporting-001", 2, 0, "some text")]
    save_index(chunks, resources, path)
    loaded, warnings = load_index(path, resources)
    assert loaded == chunks and warnings == []


def test_missing_index_is_not_an_error(tmp_path, resources):
    assert load_index(tmp_path / "nope.json", resources) == ([], [])


def test_unreadable_index_warns(tmp_path, resources):
    path = tmp_path / "chunks.json"
    path.write_text("{oops", encoding="utf-8")
    chunks, warnings = load_index(path, resources)
    assert chunks == [] and "rebuild" in warnings[0]


def test_stale_chunks_are_dropped(tmp_path, resources):
    path = tmp_path / "chunks.json"
    path.write_text(json.dumps({"chunks": [
        {"resource_id": "placeholder-reporting-001", "source_url": "https://example.org/placeholder/reporting.pdf",
         "page": 1, "chunk_index": 0, "text": "kept"},
        {"resource_id": "placeholder-reporting-001", "source_url": "https://example.org/OLD-URL.pdf",
         "page": 1, "chunk_index": 1, "text": "url changed"},
        {"resource_id": "removed-from-catalog", "source_url": "https://example.org/x",
         "page": 1, "chunk_index": 0, "text": "orphan"},
    ]}), encoding="utf-8")
    chunks, warnings = load_index(path, resources)
    assert [c.text for c in chunks] == ["kept"]
    assert "Ignored 2" in warnings[0]
