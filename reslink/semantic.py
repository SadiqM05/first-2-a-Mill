"""Local semantic search over verified content with ChromaDB + its built-in ONNX MiniLM model.

What is embedded (and nothing else):
- catalog metadata for every verified resource: title, category, description, keywords
  (never URLs, never portal contents; portals only contribute their catalog metadata);
- extracted text chunks of public documents (``content_type == "pdf"``) from chunks.json.

The index lives in ``data/index/chroma`` (git-ignored) and is fully rebuilt by
``python -m scripts.build_index``. A fingerprint of everything embedded is stored on the
collection; if it no longer matches the current catalog + chunks, the index is treated
as stale and the app falls back to keyword retrieval.

Semantic similarity only *nominates* evidence. Whether an answer is supported is still
decided downstream (Gemini's sufficient flag + citation validation).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from reslink.models import Chunk, Resource

# Telemetry off: also passed explicitly as Settings(anonymized_telemetry=False) below.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

COLLECTION_NAME = "reslink"
EMBEDDING_MODEL = "chroma-onnx/all-MiniLM-L6-v2"
SCHEMA_VERSION = 1

# Cosine-distance cutoffs above which semantic hits are discarded as noise, tuned with
# `python -m scripts.compare_retrieval --sweep` on tests/eval_questions.json (docs/EVALUATION.md).
# They remove clearly unrelated text; they do NOT decide whether a question is answerable
# (supported and unsupported questions overlap in distance, so no cutoff can).
# - documents: 0.75 kept every supported target page in the eval set.
# - catalog metadata: tighter, because the 2nd/3rd nearest catalog entries were almost always
#   irrelevant while correct top-1 matches were mostly <= 0.65.
DEFAULT_MAX_DISTANCE = 0.75
CATALOG_MAX_DISTANCE = 0.65

CATALOG_KIND = "catalog"
DOCUMENT_KIND = "document"


@dataclass(frozen=True)
class SemanticHit:
    kind: str  # "catalog" or "document"
    resource_id: str
    distance: float
    page: int | None = None
    chunk_index: int | None = None


@dataclass(frozen=True)
class IndexDocument:
    id: str
    text: str
    metadata: dict


def catalog_text(resource: Resource) -> str:
    """Text embedded for a catalog entry. Metadata only; no URL."""
    parts = [resource.title, resource.category_label, resource.description, ", ".join(resource.keywords)]
    return ". ".join(p for p in parts if p)


def build_documents(resources: list[Resource], chunks: list[Chunk]) -> list[IndexDocument]:
    """Everything that goes into the vector index, with stable IDs and citation metadata."""
    by_id = {r.id: r for r in resources}
    docs = [
        IndexDocument(
            id=f"catalog:{r.id}",
            text=catalog_text(r),
            metadata={"kind": CATALOG_KIND, "resource_id": r.id},
        )
        for r in resources
    ]
    for c in chunks:
        resource = by_id.get(c.resource_id)
        # Only public documents are embedded; a chunk tied to a portal (or to nothing) is never indexed.
        if resource is None or resource.content_type != "pdf" or not c.text.strip():
            continue
        docs.append(
            IndexDocument(
                id=f"doc:{c.resource_id}@p{c.page}#c{c.chunk_index}",
                text=c.text,
                metadata={
                    "kind": DOCUMENT_KIND,
                    "resource_id": c.resource_id,
                    "page": c.page if c.page is not None else -1,
                    "chunk_index": c.chunk_index,
                },
            )
        )
    return docs


def fingerprint(docs: list[IndexDocument]) -> str:
    """Hash of model + schema + every embedded document. Any change marks the index stale."""
    h = hashlib.sha256(f"{EMBEDDING_MODEL}|{SCHEMA_VERSION}".encode())
    for d in sorted(docs, key=lambda d: d.id):
        h.update(json.dumps([d.id, d.text, d.metadata], sort_keys=True).encode())
    return h.hexdigest()


def _embedding_function():
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    return ONNXMiniLM_L6_V2()


def model_is_cached() -> bool:
    """True if the ONNX model files exist locally (so loading it won't trigger a download)."""
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2 as EF
    except ImportError:
        return False
    folder = Path(EF.DOWNLOAD_PATH) / EF.EXTRACTED_FOLDER_NAME
    return all((folder / f).is_file() for f in ("model.onnx", "tokenizer.json", "vocab.txt"))


def _client(path: Path):
    import chromadb
    from chromadb.config import Settings

    return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))


class SemanticIndex:
    """Query wrapper around a validated Chroma collection."""

    def __init__(self, collection):
        self._collection = collection
        self._embedding_function = _embedding_function()
        self._last_query: tuple[str, list] | None = None  # reuse the embedding across kind-filtered searches

    def _embed(self, query: str) -> list:
        if self._last_query is None or self._last_query[0] != query:
            self._last_query = (query, self._embedding_function([query])[0])
        return self._last_query[1]

    def search(
        self, query: str, n: int = 8, max_distance: float = DEFAULT_MAX_DISTANCE, kind: str | None = None
    ) -> list[SemanticHit]:
        """Nearest catalog entries and/or document chunks, closest first, within max_distance.

        ``kind`` ("catalog" or "document") searches one kind only, so short catalog metadata
        isn't crowded out by longer document chunks.
        """
        result = self._collection.query(
            query_embeddings=[self._embed(query)],
            n_results=min(n, self._collection.count()),
            where={"kind": kind} if kind else None,
            include=["metadatas", "distances"],
        )
        hits = []
        for meta, dist in zip(result["metadatas"][0], result["distances"][0]):
            if dist > max_distance:
                continue
            page = meta.get("page")
            hits.append(SemanticHit(
                kind=meta["kind"], resource_id=meta["resource_id"], distance=float(dist),
                page=None if page in (None, -1) else int(page), chunk_index=meta.get("chunk_index"),
            ))
        return hits

    @classmethod
    def build(cls, path: Path, resources: list[Resource], chunks: list[Chunk]) -> "SemanticIndex":
        """(Re)create the collection from scratch. May download the model on first use."""
        docs = build_documents(resources, chunks)
        client = _client(path)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:  # collection didn't exist
            pass
        collection = client.create_collection(
            COLLECTION_NAME,
            embedding_function=_embedding_function(),
            metadata={"hnsw:space": "cosine", "fingerprint": fingerprint(docs), "model": EMBEDDING_MODEL},
        )
        if docs:
            collection.add(ids=[d.id for d in docs], documents=[d.text for d in docs],
                           metadatas=[d.metadata for d in docs])
        return cls(collection)

    @classmethod
    def open(cls, path: Path, resources: list[Resource], chunks: list[Chunk]) -> tuple["SemanticIndex | None", str]:
        """Open an existing index if it is present, current, and usable offline.

        Returns (index, status). index is None whenever semantic retrieval must be skipped;
        status explains why (shown in the sidebar).
        """
        try:
            import chromadb  # noqa: F401
        except ImportError:
            return None, "ChromaDB not installed"
        if not Path(path).is_dir():
            return None, "semantic index not built (run: python -m scripts.build_index)"
        if not model_is_cached():
            return None, "embedding model not downloaded (run: python -m scripts.build_index)"
        try:
            collection = _client(path).get_collection(COLLECTION_NAME, embedding_function=_embedding_function())
        except Exception:
            return None, "semantic index missing or unreadable (run: python -m scripts.build_index)"
        expected = fingerprint(build_documents(resources, chunks))
        if (collection.metadata or {}).get("fingerprint") != expected:
            return None, "semantic index is stale (run: python -m scripts.build_index)"
        return cls(collection), "ready"
