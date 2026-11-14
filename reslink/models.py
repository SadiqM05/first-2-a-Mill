"""Plain data types shared across ResLink modules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

# Initial categories from docs/PRD.md. Adjust once real resources are collected.
CATEGORIES: dict[str, str] = {
    "maintenance": "Maintenance",
    "reporting": "Reporting",
    "programming": "Programming",
    "policies": "Policies",
    "ra_portals": "RA Portals",
    "procedures": "Procedures",
}

# "portal" = sign-in-only system: linkable, but its content can't be read or indexed.
# "transcription" = a local Markdown transcription with no public URL (e.g. photographed manual
#   pages). Its text is indexed from `source_path`; it is never shown as a clickable link.
CONTENT_TYPES: tuple[str, ...] = ("webpage", "pdf", "form", "portal", "transcription")


def slugify(text: str) -> str:
    """Stable, readable ID fragment: 'Checking IN Packages' -> 'checking-in-packages'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass(frozen=True)
class Resource:
    """One verified entry from data/resources.json."""

    id: str
    title: str
    category: str
    url: str | None  # None only for content_type "transcription"
    content_type: str = "webpage"
    description: str = ""
    keywords: tuple[str, ...] = field(default_factory=tuple)
    source_path: str | None = None  # transcriptions only: repo-relative Markdown path

    @property
    def category_label(self) -> str:
        return CATEGORIES.get(self.category, self.category.title())

    @property
    def requires_login(self) -> bool:
        return self.content_type == "portal"

    @property
    def is_transcription(self) -> bool:
        return self.content_type == "transcription"


@dataclass(frozen=True)
class Chunk:
    """A passage of text from a catalog resource's document.

    PDF chunks: ``page`` is the PDF page index; ``section`` is None.
    Procedure units (transcriptions): one whole procedure; ``section`` is its heading,
    ``page``..``page_end`` the printed manual page range inherited from its group.
    """

    resource_id: str
    page: int | None
    chunk_index: int
    text: str
    section: str | None = None
    page_end: int | None = None
    group: str | None = None
    incomplete: str | None = None  # source-limitation text when the source pages are incomplete
    review: tuple[str, ...] = ()  # passages flagged for manual verification
    related: tuple[str, ...] = ()  # catalog IDs of verified resources this procedure uses

    @property
    def unit_key(self) -> tuple[str, int | None, str | None]:
        """The citation unit this chunk belongs to (a PDF page, or a procedure section)."""
        return (self.resource_id, self.page, self.section)


def page_label(page: int | None, page_end: int | None) -> str:
    if page is None:
        return ""
    if page_end is not None and page_end != page:
        return f"pp. {page}–{page_end}"
    return f"p. {page}"


@dataclass(frozen=True)
class Evidence:
    """One retrieved piece of support for an answer, always tied to a catalog resource."""

    resource: Resource
    text: str
    score: float
    page: int | None = None
    source: str = "catalog"  # "catalog" (metadata) or "document" (extracted text)
    section: str | None = None
    page_end: int | None = None
    incomplete: str | None = None
    review: tuple[str, ...] = ()
    related: tuple[Resource, ...] = ()  # resolved from the catalog, never from model output

    @property
    def evidence_id(self) -> str:
        """Stable ID the model cites.

        PDF pages: 'ra-job-description@p4'. Procedures: 'front-desk-manual#checking-in-packages'.
        """
        if self.source == "document" and self.section:
            return f"{self.resource.id}#{slugify(self.section)}"
        if self.source == "document" and self.page is not None:
            return f"{self.resource.id}@p{self.page}"
        return self.resource.id


@dataclass(frozen=True)
class Citation:
    """A verified source the answer relied on: a catalog resource plus optional page/section."""

    resource: Resource
    page: int | None = None
    section: str | None = None
    page_end: int | None = None

    @property
    def link(self) -> str | None:
        """Catalog URL (with a page anchor for PDFs), or None for sources without a public URL."""
        url = self.resource.url
        if url is None:
            return None
        if self.page is not None and self.resource.content_type == "pdf" and "#" not in url:
            return f"{url}#page={self.page}"
        return url

    @property
    def label(self) -> str:
        """Human-readable citation, e.g. 'Front Desk Residence Hall Manual, § Checking IN Packages, pp. 30–32'."""
        parts = [self.resource.title]
        if self.section:
            parts.append(f"§ {self.section}")
        pages = page_label(self.page, self.page_end)
        if pages:
            parts.append(pages)
        return ", ".join(parts)


NOTE_UNVERIFIED = "unverified"  # source not verified as current: compact note beneath Sources
NOTE_UNVERIFIED_LINK = "unverified_link"  # source mentions an unverified web address: compact note
NOTE_INCOMPLETE = "incomplete"  # source pages incomplete: prominent warning
NOTE_REVIEW = "review"  # passage possibly transcribed incorrectly: prominent warning
PROMINENT_NOTES = frozenset({NOTE_INCOMPLETE, NOTE_REVIEW})


@dataclass(frozen=True)
class Note:
    """A source-quality notice added by code (never by the model)."""

    kind: str
    text: str

    @property
    def prominent(self) -> bool:
        return self.kind in PROMINENT_NOTES


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
    caveats: tuple[Note, ...] = ()  # source-quality notices added by code (see Note kinds)
    privacy_blocked: bool = False  # True when the message was blocked by the privacy check
