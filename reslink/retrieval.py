"""Evidence retrieval. Keyword retrieval over catalog metadata and document chunks; semantic (ChromaDB) later.

Every retriever returns ``Evidence`` tied to a validated catalog ``Resource``, so
anything shown downstream can be traced to a verified entry.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Hashable, Protocol, TypeVar

from reslink.models import Chunk, Evidence, Resource, page_label
from reslink.procedures import neutralize_urls

if TYPE_CHECKING:
    from reslink.semantic import SemanticHit

T = TypeVar("T", bound=Hashable)
UnitKey = tuple[str, "int | None", "str | None"]

# Words that carry no signal for matching RA questions to resources.
STOPWORDS = frozenset(
    """
    a an and are as at be but by can could do does did for from get got has have
    help how i i'm im in into is it its me my need needs of on or our please should
    so some someone something that the their them there they this to up us was we
    what when where which who why will with would you your ra ras
    resident residents
    """.split()
)

KEYWORD_PHRASE_WEIGHT = 3.0  # multi-word catalog keyword appears as a phrase
KEYWORD_TOKEN_WEIGHT = 2.0  # single-word catalog keyword appears
TITLE_WEIGHT = 1.0  # per query token found in the title
CATEGORY_WEIGHT = 1.0  # per query token found in the category label
DESCRIPTION_WEIGHT = 0.5  # per query token found in the description


class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]: ...


def _stem(token: str) -> str:
    """Very light suffix stripping so 'repairs'/'repairing'/'repaired' match 'repair'."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords, stem. Order is preserved."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words if w not in STOPWORDS]


def _contains_phrase(tokens: list[str], phrase: list[str]) -> bool:
    n = len(phrase)
    return n > 0 and any(tokens[i : i + n] == phrase for i in range(len(tokens) - n + 1))


def procedure_evidence_text(resource: Resource, chunk: Chunk, body: str) -> str:
    """Evidence block for one whole procedure, with its source status stated up front.

    Web addresses inside the transcription are replaced: links are only ever shown from the catalog.
    """
    lines = [f"Source: {resource.title}, § {chunk.section}, {page_label(chunk.page, chunk.page_end)}"
             + (f" (group: {chunk.group})" if chunk.group and chunk.group != chunk.section else "")]
    if resource.is_transcription:
        lines.append("Source status: transcription of photographed manual pages; not independently verified as current.")
    if chunk.incomplete:
        lines.append(f"INCOMPLETE SOURCE: {chunk.incomplete}")
    for note in chunk.review:
        lines.append(f"FLAGGED FOR REVIEW: {note}")
    lines.append(neutralize_urls(body))
    return "\n".join(lines)


def evidence_text(resource: Resource) -> str:
    """Catalog metadata given to the model as evidence. URLs are deliberately excluded."""
    lines = [
        f"Title: {resource.title}",
        f"Category: {resource.category_label}",
        f"Type: {resource.content_type}" + (" (sign-in required)" if resource.requires_login else ""),
    ]
    if resource.description:
        lines.append(f"Description: {resource.description}")
    if resource.keywords:
        lines.append(f"Keywords: {', '.join(resource.keywords)}")
    return "\n".join(lines)


class KeywordRetriever:
    """Keyword retrieval over catalog metadata and (optionally) extracted document chunks.

    Catalog hits and document hits are ranked separately (their scores aren't comparable)
    and returned catalog-first: up to ``top_k`` of each.
    """

    def __init__(
        self,
        resources: list[Resource],
        chunks: list[Chunk] | None = None,
        min_score: float = 2.0,
    ):
        self.resources = list(resources)
        self.min_score = min_score
        self._by_id = {r.id: r for r in self.resources}
        # Chunks whose resource isn't in the catalog are ignored: every evidence must be verifiable.
        self.chunks = [c for c in (chunks or []) if c.resource_id in self._by_id]
        # Procedure headings are searchable too ("recore", "checking in packages").
        self._chunk_tokens = [set(tokenize(f"{c.section or ''} {c.text}")) for c in self.chunks]
        self._chunk_lookup = {(c.resource_id, c.page, c.chunk_index): c for c in self.chunks}
        n = len(self.chunks)
        df: dict[str, int] = {}
        for tokens in self._chunk_tokens:
            for t in tokens:
                df[t] = df.get(t, 0) + 1
        # BM25-style IDF: words in every chunk ("hall", "staff") count for little.
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def score(self, query: str, resource: Resource) -> float:
        query_tokens = tokenize(query)
        if not query_tokens:
            return 0.0
        unique = set(query_tokens)
        total = 0.0
        for keyword in resource.keywords:
            phrase = tokenize(keyword)
            if len(phrase) > 1 and _contains_phrase(query_tokens, phrase):
                total += KEYWORD_PHRASE_WEIGHT
            elif len(phrase) == 1 and phrase[0] in unique:
                total += KEYWORD_TOKEN_WEIGHT
        # Each query token counts once, at its strongest field, so a word that appears in
        # both title and category (e.g. "report" / "Reporting") isn't double-counted.
        title = set(tokenize(resource.title))
        category = set(tokenize(resource.category_label))
        description = set(tokenize(resource.description))
        for token in unique:
            if token in title:
                total += TITLE_WEIGHT
            elif token in category:
                total += CATEGORY_WEIGHT
            elif token in description:
                total += DESCRIPTION_WEIGHT
        return total

    def score_chunk(self, query: str, index: int) -> tuple[float, int]:
        """Return (IDF-weighted overlap, number of distinct query tokens matched)."""
        matched = set(tokenize(query)) & self._chunk_tokens[index]
        return sum(self._idf.get(t, 0.0) for t in matched), len(matched)

    def retrieve_catalog(self, query: str, top_k: int = 3) -> list[Evidence]:
        scored = [(self.score(query, r), r) for r in self.resources]
        hits = [(s, r) for s, r in scored if s >= self.min_score]
        hits.sort(key=lambda pair: (-pair[0], pair[1].title.lower()))
        return [Evidence(resource=r, text=evidence_text(r), score=s) for s, r in hits[:top_k]]

    def rank_pages(self, query: str) -> list[tuple[UnitKey, float, list[Chunk]]]:
        """Keyword-ranked citation units, best first: [(unit_key, score, matching chunks)].

        A unit is a PDF page, or one whole procedure (see Chunk.unit_key).
        """
        query_unique = set(tokenize(query))
        if not query_unique or not self.chunks:
            return []
        # Short questions need every word to match; longer ones at least two.
        needed = min(2, len(query_unique))
        # Citations are page-level, so matching chunks are grouped by page: one evidence
        # per page (ranked by its best chunk), containing every matching chunk of that page.
        # Keeping only the best chunk would drop answers that sit in a lower-scoring chunk.
        pages: dict[UnitKey, tuple[float, int, list[Chunk]]] = {}
        for i, chunk in enumerate(self.chunks):
            score, matched = self.score_chunk(query, i)
            if matched < needed or score <= 0:
                continue
            key = chunk.unit_key
            best, first, group = pages.get(key, (0.0, i, []))
            pages[key] = (max(best, score), min(first, i), group + [chunk])
        ranked = sorted(pages.items(), key=lambda kv: (-kv[1][0], kv[1][1]))
        return [(key, score, group) for key, (score, _, group) in ranked]

    def chunk(self, resource_id: str, page: int | None, chunk_index: int) -> Chunk | None:
        return self._chunk_lookup.get((resource_id, page, chunk_index))

    def page_evidence(self, chunks: list[Chunk], score: float) -> Evidence:
        """One document evidence block for a citation unit, from its chunks (deduplicated, in order).

        Procedures are always a single whole chunk, so a procedure reaches the model complete.
        """
        unique = {c.chunk_index: c for c in chunks}
        ordered = [unique[i] for i in sorted(unique)]
        first = ordered[0]
        resource = self._by_id[first.resource_id]
        body = "\n...\n".join(c.text for c in ordered)
        if first.section is None:  # PDF page
            return Evidence(resource, f"Source: {resource.title}, page {first.page}\n{body}", score,
                            page=first.page, source="document")
        return Evidence(
            resource, procedure_evidence_text(resource, first, body), score, page=first.page,
            source="document", section=first.section, page_end=first.page_end,
            incomplete=first.incomplete, review=first.review,
            related=tuple(self._by_id[r] for r in first.related if r in self._by_id),
        )

    def retrieve_documents(self, query: str, top_k: int = 3) -> list[Evidence]:
        return [self.page_evidence(group, score) for _, score, group in self.rank_pages(query)[:top_k]]

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        return self.retrieve_catalog(query, top_k) + self.retrieve_documents(query, top_k)


# --- Hybrid retrieval ---------------------------------------------------------------------

RRF_K = 60  # standard reciprocal-rank-fusion constant; dampens the advantage of rank 1


class SemanticSearch(Protocol):
    def search(
        self, query: str, n: int = 8, max_distance: float = ..., kind: str | None = None
    ) -> list[SemanticHit]: ...


def rrf_fuse(rankings: list[list[T]]) -> list[tuple[T, float]]:
    """Reciprocal rank fusion: score(item) = sum over rankings of 1 / (RRF_K + rank).

    Items found by several rankers outrank items found by one. Ties break by the best
    rank the item achieved, then by first appearance, so the order is deterministic.
    """
    scores: dict[T, float] = {}
    best_rank: dict[T, int] = {}
    order: dict[T, int] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (RRF_K + rank)
            best_rank[item] = min(best_rank.get(item, rank), rank)
            order.setdefault(item, len(order))
    return sorted(scores.items(), key=lambda kv: (-kv[1], best_rank[kv[0]], order[kv[0]]))


class HybridRetriever:
    """Keyword + semantic retrieval merged with reciprocal rank fusion.

    Catalog evidence and document evidence are fused separately and stay distinct.
    Semantic hits are mapped onto existing catalog IDs / indexed chunks; anything that
    doesn't resolve to a verified catalog resource is dropped. If semantic search is
    unavailable or raises, results are exactly the keyword retriever's.
    """

    def __init__(
        self,
        keyword: KeywordRetriever,
        semantic: SemanticSearch | None = None,
        *,
        max_distance: float | None = None,
        catalog_max_distance: float | None = None,
        doc_top_k: int = 3,
        keyword_pages: int = 3,
        semantic_catalog_n: int = 1,
        semantic_chunk_n: int = 8,
        semantic_pages: int = 1,
    ):
        # Defaults chosen with scripts/compare_retrieval.py (docs/EVALUATION.md). semantic_pages
        # went 2 -> 1 in Milestone 4: with procedure units added, 2 let semantic pages push a
        # keyword-found PDF target out of the top 3; 1 kept recall and reduced off-target evidence.
        self.keyword = keyword
        self.semantic = semantic
        self.max_distance = max_distance  # document chunks
        self.catalog_max_distance = catalog_max_distance  # catalog metadata
        self.doc_top_k = doc_top_k  # max document pages returned (after fusion)
        self.keyword_pages = keyword_pages  # keyword page candidates entering fusion
        self.semantic_catalog_n = semantic_catalog_n  # semantic catalog candidates entering fusion
        self.semantic_chunk_n = semantic_chunk_n  # nearest chunks fetched...
        self.semantic_pages = semantic_pages  # ...grouped into at most this many page candidates
        self.last_mode = "hybrid" if semantic is not None else "keyword"

    def _keyword_only(self, query: str, top_k: int, mode: str) -> list[Evidence]:
        self.last_mode = mode
        return self.keyword.retrieve(query, top_k)

    def _search(self, query: str, kind: str, n: int) -> list[SemanticHit]:
        kwargs = {"n": n, "kind": kind}
        limit = self.catalog_max_distance if kind == "catalog" else self.max_distance
        if limit is not None:
            kwargs["max_distance"] = limit
        hits = self.semantic.search(query, **kwargs)
        # Only hits that resolve to a verified catalog resource (and the requested kind) count.
        return [h for h in hits if h.kind == kind and h.resource_id in self.keyword._by_id]

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        if self.semantic is None or not query.strip():
            return self._keyword_only(query, top_k, "keyword")
        try:
            catalog_hits = self._search(query, "catalog", self.semantic_catalog_n)
            chunk_hits = self._search(query, "document", self.semantic_chunk_n)
        except Exception:  # broken index, model error, etc.: never break answering
            return self._keyword_only(query, top_k, "keyword (semantic error)")
        self.last_mode = "hybrid"
        by_id = self.keyword._by_id

        # Catalog: fuse keyword ranking with semantic catalog-metadata ranking.
        kw_catalog = [e.resource.id for e in self.keyword.retrieve_catalog(query, top_k)]
        sem_catalog = list(dict.fromkeys(h.resource_id for h in catalog_hits))
        catalog = [
            Evidence(resource=by_id[rid], text=evidence_text(by_id[rid]), score=score)
            for rid, score in rrf_fuse([kw_catalog, sem_catalog])[:top_k]
        ]

        # Documents: fuse keyword page ranking with semantic page ranking (page = citation unit).
        kw_pages = self.keyword.rank_pages(query)[: self.keyword_pages]
        page_chunks: dict[UnitKey, list[Chunk]] = {key: list(g) for key, _, g in kw_pages}
        sem_pages: list[UnitKey] = []
        for h in chunk_hits:
            if h.chunk_index is None:
                continue
            chunk = self.keyword.chunk(h.resource_id, h.page, h.chunk_index)
            if chunk is None:  # index and chunks.json disagree: ignore the hit
                continue
            key = chunk.unit_key
            if key not in sem_pages:
                if len(sem_pages) >= self.semantic_pages:
                    continue
                sem_pages.append(key)
            page_chunks.setdefault(key, []).append(chunk)
        documents = [
            self.keyword.page_evidence(page_chunks[key], score)
            for key, score in rrf_fuse([[k for k, _, _ in kw_pages], sem_pages])[: self.doc_top_k]
        ]
        return catalog + documents
