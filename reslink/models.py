"""Plain data types shared across ResLink modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Initial categories from docs/PRD.md. Adjust once real resources are collected.
CATEGORIES: dict[str, str] = {
    "maintenance": "Maintenance",
    "reporting": "Reporting",
    "programming": "Programming",
    "policies": "Policies",
    "ra_portals": "RA Portals",
}

# "portal" = sign-in-only system: linkable, but its content can't be read or indexed.
CONTENT_TYPES: tuple[str, ...] = ("webpage", "pdf", "form", "portal")


@dataclass(frozen=True)
class Resource:
    """One verified entry from data/resources.json."""

    id: str
    title: str
    category: str
    url: str
    content_type: str = "webpage"
    description: str = ""
    keywords: tuple[str, ...] = field(default_factory=tuple)

    @property
    def category_label(self) -> str:
        return CATEGORIES.get(self.category, self.category.title())

    @property
    def requires_login(self) -> bool:
        return self.content_type == "portal"


@dataclass(frozen=True)
class Chunk:
    """A passage of text extracted from a catalog resource's public document."""

    resource_id: str
    page: int | None
    chunk_index: int
    text: str


@dataclass(frozen=True)
class Evidence:
    """One retrieved piece of support for an answer, always tied to a catalog resource."""

    resource: Resource
    text: str
    score: float
    page: int | None = None
    source: str = "catalog"  # "catalog" (metadata) or "document" (extracted text)

    @property
    def evidence_id(self) -> str:
        """Stable ID the model cites. Page-level for documents, e.g. 'ra-job-description@p4'."""
        if self.source == "document" and self.page is not None:
            return f"{self.resource.id}@p{self.page}"
        return self.resource.id


@dataclass(frozen=True)
class Citation:
    """A verified source the answer relied on: a catalog resource plus optional page."""

    resource: Resource
    page: int | None = None

    @property
    def link(self) -> str:
        """Catalog URL, with a page anchor for PDFs. Always built from catalog data."""
        if self.page is not None and self.resource.content_type == "pdf" and "#" not in self.resource.url:
            return f"{self.resource.url}#page={self.page}"
        return self.resource.url


class Status(str, Enum):
    GROUNDED = "grounded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ERROR = "error"


@dataclass(frozen=True)
class AssistantResponse:
    """What the assistant hands to the UI. Resources/citations come from the catalog, never the model."""

    status: Status
    answer: str | None = None
    resources: tuple[Resource, ...] = ()
    citations: tuple[Citation, ...] = ()
    notice: str | None = None
