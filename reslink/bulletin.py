"""Staff Bulletin: read-only announcements from a local JSON file (no UI, no AI).

This module is deliberately independent of Larry and the retrieval/RAG pipeline:
nothing in retrieval, semantic, assistant, ingest, or procedures imports it, and
announcements are never indexed or sent to Gemini.

File format (data/bulletins.json):

    {
      "demo_data": true,                        # optional, default false
      "notice": "Fictional demonstration ...",  # optional banner text
      "announcements": [
        {"id": "demo-001", "title": "...", "description": "...",
         "category": "meetings",                # meetings | deadlines | programming | general
         "published": "2026-11-10",             # YYYY-MM-DD, required
         "due": "2026-11-20",                   # YYYY-MM-DD, optional (shown, never used for sorting)
         "pinned": false}                       # optional, default false
      ]
    }

Validation is strict and all-or-nothing, reporting every problem (like the resource catalog).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

BULLETIN_CATEGORIES: dict[str, str] = {
    "meetings": "Meetings",
    "deadlines": "Deadlines",
    "programming": "Programming",
    "general": "General",
}

_REQUIRED = ("id", "title", "description", "category", "published")
_OPTIONAL = ("due", "pinned")
_TOP_LEVEL = frozenset({"demo_data", "notice", "announcements"})


class BulletinError(ValueError):
    """Raised when the bulletin file is invalid; ``errors`` lists every problem."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid bulletin file:\n- " + "\n- ".join(errors))


@dataclass(frozen=True)
class Announcement:
    id: str
    title: str
    description: str
    category: str
    published: date
    due: date | None = None
    pinned: bool = False

    @property
    def category_label(self) -> str:
        return BULLETIN_CATEGORIES[self.category]


@dataclass(frozen=True)
class Bulletin:
    announcements: tuple[Announcement, ...] = ()
    demo_data: bool = False
    notice: str | None = None
    source_missing: bool = False  # True when the bulletin file does not exist


def _parse_date(value: Any) -> date | None:
    """Strict YYYY-MM-DD only (rejects other ISO forms like '20261110' or '2026-11-10T09:00')."""
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate(raw: Any, index: int) -> tuple[Announcement | None, list[str]]:
    where = f"announcement {index}"
    if not isinstance(raw, dict):
        return None, [f"{where}: must be a JSON object"]
    if isinstance(raw.get("id"), str) and raw["id"].strip():
        where = f"announcement {index} ({raw['id'].strip()!r})"

    errors: list[str] = []
    for name in _REQUIRED:
        if not isinstance(raw.get(name), str) or not raw[name].strip():
            errors.append(f"{where}: '{name}' is required and must be a non-empty string")
    unknown = sorted(set(raw) - set(_REQUIRED) - set(_OPTIONAL))
    if unknown:
        errors.append(f"{where}: unknown field(s) {unknown}")

    category = raw.get("category")
    if isinstance(category, str) and category.strip() and category.strip() not in BULLETIN_CATEGORIES:
        errors.append(f"{where}: category {category!r} must be one of {list(BULLETIN_CATEGORIES)}")

    published = _parse_date(raw.get("published"))
    if isinstance(raw.get("published"), str) and raw["published"].strip() and published is None:
        errors.append(f"{where}: 'published' must be a date in YYYY-MM-DD format")

    due = None
    if "due" in raw:
        due = _parse_date(raw["due"])
        if due is None:
            errors.append(f"{where}: 'due' must be a date in YYYY-MM-DD format")

    pinned = raw.get("pinned", False)
    if not isinstance(pinned, bool):
        errors.append(f"{where}: 'pinned' must be true or false")

    if errors:
        return None, errors
    return Announcement(
        id=raw["id"].strip(), title=raw["title"].strip(), description=raw["description"].strip(),
        category=raw["category"].strip(), published=published, due=due, pinned=pinned,
    ), []


def parse_bulletin(data: Any) -> Bulletin:
    """Validate decoded JSON and return a Bulletin, or raise BulletinError."""
    if not isinstance(data, dict):
        raise BulletinError(["bulletin file must be a JSON object with an 'announcements' list"])
    errors: list[str] = []
    unknown = sorted(set(data) - _TOP_LEVEL)
    if unknown:
        errors.append(f"unknown top-level field(s) {unknown}")
    demo_data = data.get("demo_data", False)
    if not isinstance(demo_data, bool):
        errors.append("'demo_data' must be true or false")
    notice = data.get("notice")
    if notice is not None and (not isinstance(notice, str) or not notice.strip()):
        errors.append("'notice' must be a non-empty string when present")
    raw_items = data.get("announcements")
    if not isinstance(raw_items, list):
        errors.append("'announcements' is required and must be a list")
        raw_items = []

    items: list[Announcement] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items):
        item, item_errors = _validate(raw, index)
        errors.extend(item_errors)
        if item is None:
            continue
        if item.id in seen:
            errors.append(f"announcement {index}: duplicate id {item.id!r}")
            continue
        seen.add(item.id)
        items.append(item)
    if errors:
        raise BulletinError(errors)
    return Bulletin(tuple(items), demo_data, notice.strip() if isinstance(notice, str) else None)


def load_bulletin(path: Path) -> Bulletin:
    """Read and validate the bulletin file. A missing file is not an error (source_missing=True)."""
    path = Path(path)
    if not path.is_file():
        return Bulletin(source_missing=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BulletinError([f"{path.name} is not valid JSON: {exc}"]) from exc
    return parse_bulletin(data)


def search(items: list[Announcement] | tuple[Announcement, ...], query: str) -> list[Announcement]:
    """Case-insensitive match on title + description; every word in the query must appear."""
    words = query.lower().split()
    if not words:
        return list(items)
    return [a for a in items if all(w in f"{a.title} {a.description}".lower() for w in words)]


def filter_by_category(items, categories) -> list[Announcement]:
    """Keep announcements in the selected categories. An empty selection means all categories."""
    selected = set(categories or ())
    return [a for a in items if not selected or a.category in selected]


def order(items) -> list[Announcement]:
    """Pinned first; within each group newest ``published`` first; ties by title then id.

    ``due`` is never used for sorting.
    """
    return sorted(items, key=lambda a: (not a.pinned, -a.published.toordinal(), a.title.lower(), a.id))


def select(bulletin: Bulletin, query: str = "", categories=()) -> list[Announcement]:
    """Search + filter + order: the list the UI shows."""
    return order(filter_by_category(search(bulletin.announcements, query), categories))


# --- Read / unread (per browser session; the JSON file is never modified) ----------------------------

STATUS_ALL = "all"
STATUS_UNREAD = "unread"
STATUS_READ = "read"
STATUSES = (STATUS_ALL, STATUS_UNREAD, STATUS_READ)


def is_read(item: Announcement, read_ids) -> bool:
    return item.id in read_ids


def filter_by_status(items, read_ids, status: str = STATUS_ALL) -> list[Announcement]:
    """Keep all, only unread, or only read announcements. Order is preserved."""
    if status == STATUS_UNREAD:
        return [a for a in items if a.id not in read_ids]
    if status == STATUS_READ:
        return [a for a in items if a.id in read_ids]
    return list(items)


def unread_count(items, read_ids) -> int:
    return sum(1 for a in items if a.id not in read_ids)


def toggle_read(read_ids: set[str], announcement_id: str) -> None:
    """Mark as read if unread, otherwise mark as unread (mutates the set)."""
    if announcement_id in read_ids:
        read_ids.discard(announcement_id)
    else:
        read_ids.add(announcement_id)
