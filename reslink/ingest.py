"""Extract and chunk public documents for catalog resources; save/load the local chunk index.

Only resources with ``content_type == "pdf"`` are ingested for now. Portals (sign-in
pages) are never ingested. The index is a local JSON file, rebuilt by
``python -m scripts.build_index`` and never committed.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from reslink.models import Chunk, Resource

CHUNK_WORDS = 250
OVERLAP_WORDS = 50
MIN_CHUNK_WORDS = 8

# Typographic characters seen in UT PDFs, mapped to plain equivalents.
_CHAR_MAP = str.maketrans({"―": '"', "—": "-", "–": "-", "‘": "'", "’": "'",
                           "“": '"', "”": '"', " ": " "})


def normalize_text(text: str) -> str:
    """NFKC-normalize, replace typographic punctuation, and collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).translate(_CHAR_MAP)
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_words: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word windows. Tiny trailing fragments are dropped."""
    if overlap >= chunk_words:
        raise ValueError("overlap must be smaller than chunk_words")
    words = normalize_text(text).split()
    if not words:
        return []
    chunks, step = [], chunk_words - overlap
    for start in range(0, len(words), step):
        window = words[start : start + chunk_words]
        if len(window) < MIN_CHUNK_WORDS and chunks:
            break
        chunks.append(" ".join(window))
        if start + chunk_words >= len(words):
            break
    return chunks


def chunk_pages(resource_id: str, pages: list[tuple[int, str]]) -> list[Chunk]:
    """Chunk each page separately so every chunk keeps an exact page citation."""
    out: list[Chunk] = []
    for page, text in pages:
        for i, piece in enumerate(chunk_text(text)):
            out.append(Chunk(resource_id=resource_id, page=page, chunk_index=i, text=piece))
    return out


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Return (1-based page number, text) for every page with text."""
    import pymupdf

    with pymupdf.open(path) as doc:
        pages = [(i + 1, page.get_text()) for i, page in enumerate(doc)]
    return [(n, t) for n, t in pages if t.strip()]


def save_index(chunks: list[Chunk], resources: list[Resource], path: Path) -> None:
    by_id = {r.id: r for r in resources}
    data = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chunks": [
            {"resource_id": c.resource_id, "source_url": by_id[c.resource_id].url,
             "page": c.page, "chunk_index": c.chunk_index, "text": c.text}
            for c in chunks
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def load_index(path: Path, resources: list[Resource]) -> tuple[list[Chunk], list[str]]:
    """Load chunks, keeping only those that still match a catalog entry and its URL.

    Returns (chunks, warnings). A missing index is not an error: it returns ([], []).
    """
    path = Path(path)
    if not path.is_file():
        return [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_chunks = data["chunks"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], [f"{path.name} is unreadable; rebuild it with: python -m scripts.build_index"]

    by_id = {r.id: r for r in resources}
    chunks, stale = [], 0
    for raw in raw_chunks:
        resource = by_id.get(raw.get("resource_id"))
        if resource is None or raw.get("source_url") != resource.url or not raw.get("text"):
            stale += 1
            continue
        chunks.append(Chunk(resource.id, raw.get("page"), int(raw.get("chunk_index", 0)), raw["text"]))
    warnings = []
    if stale:
        warnings.append(
            f"Ignored {stale} indexed passage(s) that no longer match the catalog; "
            "rebuild with: python -m scripts.build_index"
        )
    return chunks, warnings
