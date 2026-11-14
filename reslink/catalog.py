"""Load and validate the verified resource catalog (data/resources.json).

Validation is strict on purpose: a resource that fails any check is never
shown, because every link in the UI must come from this catalog.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from reslink.models import CATEGORIES, CONTENT_TYPES, Resource

REQUIRED_FIELDS = ("id", "title", "category", "url")
OPTIONAL_FIELDS = ("content_type", "description", "keywords")
ALLOWED_FIELDS = frozenset(REQUIRED_FIELDS + OPTIONAL_FIELDS)

# Hosts reserved for documentation/test data. These are used by test fixtures
# and must never be surfaced as real university resources.
PLACEHOLDER_HOSTS = frozenset({"example.org", "example.com", "example.net"})


class CatalogError(ValueError):
    """Raised when the catalog cannot be loaded; ``errors`` lists every problem."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid resource catalog:\n- " + "\n- ".join(errors))


def _is_placeholder_host(host: str) -> bool:
    return any(host == h or host.endswith("." + h) for h in PLACEHOLDER_HOSTS)


def _validate_url(url: str, allow_placeholders: bool) -> str | None:
    """Return an error message for ``url``, or None if it is acceptable."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return f"url must be an absolute https:// URL (got {url!r})"
    host = (parsed.hostname or "").lower()
    if not allow_placeholders and _is_placeholder_host(host):
        return f"url uses placeholder host {host!r}; only verified sources belong in the catalog"
    return None


def _validate_entry(
    raw: Any, index: int, allow_placeholders: bool
) -> tuple[Resource | None, list[str]]:
    where = f"entry {index}"
    if not isinstance(raw, dict):
        return None, [f"{where}: must be a JSON object"]

    if isinstance(raw.get("id"), str) and raw["id"].strip():
        where = f"entry {index} ({raw['id'].strip()!r})"

    errors: list[str] = []
    for name in REQUIRED_FIELDS:
        value = raw.get(name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}: '{name}' is required and must be a non-empty string")

    unknown = sorted(set(raw) - ALLOWED_FIELDS)
    if unknown:
        errors.append(f"{where}: unknown field(s) {unknown}")

    category = raw.get("category")
    if isinstance(category, str) and category.strip() and category.strip() not in CATEGORIES:
        errors.append(f"{where}: category {category!r} must be one of {sorted(CATEGORIES)}")

    url = raw.get("url")
    if isinstance(url, str) and url.strip():
        url_error = _validate_url(url.strip(), allow_placeholders)
        if url_error:
            errors.append(f"{where}: {url_error}")

    content_type = raw.get("content_type", "webpage")
    if content_type not in CONTENT_TYPES:
        errors.append(f"{where}: content_type {content_type!r} must be one of {list(CONTENT_TYPES)}")

    description = raw.get("description", "")
    if not isinstance(description, str):
        errors.append(f"{where}: 'description' must be a string")

    keywords = raw.get("keywords", [])
    if not isinstance(keywords, list) or not all(
        isinstance(k, str) and k.strip() for k in keywords
    ):
        errors.append(f"{where}: 'keywords' must be a list of non-empty strings")

    if errors:
        return None, errors

    return (
        Resource(
            id=raw["id"].strip(),
            title=raw["title"].strip(),
            category=raw["category"].strip(),
            url=raw["url"].strip(),
            content_type=content_type,
            description=description.strip(),
            keywords=tuple(k.strip() for k in keywords),
        ),
        [],
    )


def parse_catalog(data: Any, *, allow_placeholders: bool = False) -> list[Resource]:
    """Validate already-decoded JSON and return resources, or raise CatalogError."""
    if not isinstance(data, list):
        raise CatalogError(["catalog must be a JSON array of resource objects"])

    resources: list[Resource] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(data):
        resource, entry_errors = _validate_entry(raw, index, allow_placeholders)
        errors.extend(entry_errors)
        if resource is None:
            continue
        if resource.id in seen_ids:
            errors.append(f"entry {index}: duplicate id {resource.id!r}")
            continue
        seen_ids.add(resource.id)
        resources.append(resource)

    if errors:
        raise CatalogError(errors)
    return resources


def load_catalog(path: Path, *, allow_placeholders: bool = False) -> list[Resource]:
    """Read and validate a catalog file. An empty array is valid."""
    path = Path(path)
    if not path.is_file():
        raise CatalogError([f"catalog file not found: {path}"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogError([f"{path.name} is not valid JSON: {exc}"]) from exc
    return parse_catalog(data, allow_placeholders=allow_placeholders)


def group_by_category(resources: list[Resource]) -> dict[str, list[Resource]]:
    """Group resources under every known category, in display order (empty lists kept)."""
    grouped: dict[str, list[Resource]] = {key: [] for key in CATEGORIES}
    for resource in resources:
        grouped[resource.category].append(resource)
    for items in grouped.values():
        items.sort(key=lambda r: r.title.lower())
    return grouped
