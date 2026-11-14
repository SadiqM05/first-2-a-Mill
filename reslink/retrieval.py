"""Evidence retrieval. Keyword retrieval over catalog metadata and document chunks; semantic (ChromaDB) later.

Every retriever returns ``Evidence`` tied to a validated catalog ``Resource``, so
anything shown downstream can be traced to a verified entry.
"""

from __future__ import annotations

import math
import re
from typing import Protocol

from reslink.models import Chunk, Evidence, Resource

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
        self._chunk_tokens = [set(tokenize(c.text)) for c in self.chunks]
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

    def retrieve_documents(self, query: str, top_k: int = 3) -> list[Evidence]:
        query_unique = set(tokenize(query))
        if not query_unique or not self.chunks:
            return []
        # Short questions need every word to match; longer ones at least two.
        needed = min(2, len(query_unique))
        # Citations are page-level, so matching chunks are grouped by page: one evidence
        # per page (ranked by its best chunk), containing every matching chunk of that page.
        # Keeping only the best chunk would drop answers that sit in a lower-scoring chunk.
        pages: dict[tuple[str, int | None], tuple[float, int, list[Chunk]]] = {}
        for i, chunk in enumerate(self.chunks):
            score, matched = self.score_chunk(query, i)
            if matched < needed or score <= 0:
                continue
            key = (chunk.resource_id, chunk.page)
            best, first, group = pages.get(key, (0.0, i, []))
            pages[key] = (max(best, score), min(first, i), group + [chunk])
        ranked = sorted(pages.values(), key=lambda v: (-v[0], v[1]))
        out: list[Evidence] = []
        for score, _, group in ranked[:top_k]:
            group.sort(key=lambda c: c.chunk_index)
            resource = self._by_id[group[0].resource_id]
            body = "\n...\n".join(c.text for c in group)
            text = f"Source: {resource.title}, page {group[0].page}\n{body}"
            out.append(Evidence(resource, text, score, page=group[0].page, source="document"))
        return out

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        return self.retrieve_catalog(query, top_k) + self.retrieve_documents(query, top_k)
