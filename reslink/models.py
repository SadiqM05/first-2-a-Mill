"""Plain data types shared across ResLink modules."""

from __future__ import annotations

from dataclasses import dataclass, field

# Initial categories from docs/PRD.md. Adjust once real resources are collected.
CATEGORIES: dict[str, str] = {
    "maintenance": "Maintenance",
    "reporting": "Reporting",
    "programming": "Programming",
    "policies": "Policies",
}

CONTENT_TYPES: tuple[str, ...] = ("webpage", "pdf", "form")


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
