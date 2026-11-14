"""Parse a Markdown procedures transcription into whole-procedure chunks.

Document structure (see data/procedures/*.md):

    # Document title
    Source note...
    ## Group name (pp. 24–26)          <- group; page range is required
    optional overview text             <- becomes "<Group> — Overview" if a group has ### procedures
    ### Procedure name                 <- one procedure = one chunk (never split)
    1. Step...
       - Sub-step...
    **Manual note:** ...
    **Source limitation:** ...         <- marks the unit incomplete

A group without any ### heading (e.g. a reference table) becomes a single unit named after
the group. Bodies are stored verbatim (numbered steps, nested lists, tables, notes).

A sidecar ``<file>.meta.json`` (validated) adds, per section title:
- "related": catalog IDs of verified resources the procedure uses (links come only from these);
- "review":  transcription passages flagged for manual verification (text is never corrected).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from reslink.models import Chunk, Resource, slugify

GROUP_RE = re.compile(r"^##\s+(?P<name>.+?)\s*\((?P<pp>pp?)\.\s*(?P<start>\d+)(?:\s*[–—-]\s*(?P<end>\d+))?\)\s*$")
PROCEDURE_RE = re.compile(r"^###\s+(?P<name>.+?)\s*$")
LIMITATION_RE = re.compile(r"\*\*Source limitation:\*\*\s*(?P<text>.+)")
URL_RE = re.compile(r"https?://\S+?(?=[)\s]|\.?$|\.\s)", re.IGNORECASE)

OVERVIEW_SUFFIX = " — Overview"
UNVERIFIED_URL_REVIEW = (
    "Contains a web address from the transcription that has not been verified by the team; "
    "it is not shown as a link."
)


class ProcedureError(ValueError):
    """Structural problem in a procedures file; ``errors`` lists every problem found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid procedures file:\n- " + "\n- ".join(errors))


@dataclass(frozen=True)
class ProcedureMeta:
    related: dict[str, tuple[str, ...]]
    review: dict[str, tuple[str, ...]]
    safety: dict[str, tuple[str, ...]] = field(default_factory=dict)
    companions: dict[str, tuple[str, ...]] = field(default_factory=dict)


def parse_procedures(markdown: str, resource_id: str) -> list[Chunk]:
    """Split the document into units. Raises ProcedureError on structural problems."""
    errors: list[str] = []
    units: list[tuple[str, str, int, int | None, list[str]]] = []  # (section, group, start, end, lines)
    group: tuple[str, int, int | None] | None = None
    group_intro: list[str] = []
    group_has_procedures = False
    current: list[str] | None = None
    current_name = ""

    def close_procedure():
        nonlocal current
        if current is not None and group is not None:
            units.append((current_name, group[0], group[1], group[2], current))
        current = None

    def close_group():
        close_procedure()
        if group is None:
            return
        intro = "\n".join(group_intro).strip()
        if not group_has_procedures:
            units.append((group[0], group[0], group[1], group[2], group_intro[:]))
        elif intro:
            units.append((group[0] + OVERVIEW_SUFFIX, group[0], group[1], group[2], group_intro[:]))

    for lineno, line in enumerate(markdown.splitlines(), start=1):
        if line.startswith("## ") or line.rstrip() == "##":
            close_group()
            m = GROUP_RE.match(line.rstrip())
            if not m:
                errors.append(f"line {lineno}: '##' heading needs a page reference like '(pp. 24–26)' or '(p. 18)': {line.strip()!r}")
                group = None
                continue
            start = int(m["start"])
            end = int(m["end"]) if m["end"] else None
            if end is not None and end < start:
                errors.append(f"line {lineno}: page range ends before it starts: {line.strip()!r}")
            group, group_intro, group_has_procedures = (m["name"].strip(), start, end), [], False
        elif line.startswith("### "):
            close_procedure()
            if group is None:
                errors.append(f"line {lineno}: '###' procedure outside a valid '##' group: {line.strip()!r}")
                continue
            current_name = PROCEDURE_RE.match(line.rstrip())["name"].strip()
            current, group_has_procedures = [], True
        elif current is not None:
            current.append(line)
        elif group is not None:
            group_intro.append(line)
    close_group()

    chunks, seen = [], {}
    for index, (section, group_name, start, end, lines) in enumerate(units):
        body = "\n".join(lines).strip()
        if not body:
            errors.append(f"section {section!r} is empty")
            continue
        slug = slugify(section)
        if slug in seen:
            errors.append(f"duplicate section {section!r} (same ID as {seen[slug]!r})")
            continue
        seen[slug] = section
        limitation = LIMITATION_RE.search(body)
        review = (UNVERIFIED_URL_REVIEW,) if URL_RE.search(body) else ()
        chunks.append(Chunk(
            resource_id=resource_id, page=start, chunk_index=index, text=body, section=section,
            page_end=end, group=group_name, incomplete=limitation["text"].strip() if limitation else None,
            review=review,
        ))
    if not chunks and not errors:
        errors.append("no '##' procedure groups found")
    if errors:
        raise ProcedureError(errors)
    return chunks


def load_meta(path: Path, sections: set[str], catalog_ids: set[str]) -> ProcedureMeta:
    """Read and validate the sidecar. Unknown sections or catalog IDs are errors."""
    if not path.is_file():
        return ProcedureMeta({}, {})
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProcedureError([f"{path.name} is not valid JSON: {exc}"]) from exc
    errors: list[str] = []
    related, review, safety = {}, {}, {}
    for key, target, check_ids in (("related", related, True), ("review", review, False), ("safety", safety, False)):
        block = data.get(key, {})
        if not isinstance(block, dict):
            errors.append(f"{path.name}: '{key}' must be an object keyed by section title")
            continue
        for section, values in block.items():
            if section not in sections:
                errors.append(f"{path.name}: {key} refers to unknown section {section!r}")
                continue
            if not isinstance(values, list) or not all(isinstance(v, str) and v.strip() for v in values):
                errors.append(f"{path.name}: {key}[{section!r}] must be a list of non-empty strings")
                continue
            if check_ids:
                unknown = [v for v in values if v not in catalog_ids]
                if unknown:
                    errors.append(f"{path.name}: related[{section!r}] has unknown catalog IDs {unknown}")
                    continue
            target[section] = tuple(v.strip() for v in values)
    companions = {}
    block = data.get("companions", {})
    if not isinstance(block, dict):
        errors.append(f"{path.name}: 'companions' must be an object keyed by section title")
        block = {}
    for section, values in block.items():
        if section not in sections:
            errors.append(f"{path.name}: companions refers to unknown section {section!r}")
        elif not isinstance(values, list) or not all(isinstance(v, str) and v in sections and v != section for v in values):
            errors.append(f"{path.name}: companions[{section!r}] must list other existing section titles")
        else:
            companions[section] = tuple(values)
    unknown_keys = set(data) - {"related", "review", "safety", "companions", "_comment"}
    if unknown_keys:
        errors.append(f"{path.name}: unknown keys {sorted(unknown_keys)}")
    if errors:
        raise ProcedureError(errors)
    return ProcedureMeta(related, review, safety, companions)


def meta_path(source: Path) -> Path:
    return source.with_name(source.stem + ".meta.json")


def load_resource_procedures(resource: Resource, root: Path, resources: list[Resource]) -> list[Chunk]:
    """Parse one transcription resource and apply its sidecar metadata."""
    source = root / resource.source_path
    if not source.is_file():
        raise ProcedureError([f"{resource.id}: source file not found: {resource.source_path}"])
    chunks = parse_procedures(source.read_text(encoding="utf-8"), resource.id)
    meta = load_meta(meta_path(source), {c.section for c in chunks}, {r.id for r in resources})
    return [
        replace(c, related=meta.related.get(c.section, ()), review=c.review + meta.review.get(c.section, ()),
                safety=" ".join(meta.safety.get(c.section, ())) or None,
                companions=meta.companions.get(c.section, ()))
        for c in chunks
    ]


def load_procedure_chunks(resources: list[Resource], root: Path) -> tuple[list[Chunk], list[str]]:
    """All procedure units for every transcription in the catalog. Problems become warnings."""
    chunks: list[Chunk] = []
    warnings: list[str] = []
    for resource in resources:
        if not resource.is_transcription:
            continue
        try:
            chunks.extend(load_resource_procedures(resource, root, resources))
        except ProcedureError as exc:
            warnings.append(f"Procedures from {resource.title} were not loaded: " + "; ".join(exc.errors))
    return chunks, warnings


def neutralize_urls(text: str) -> str:
    """Replace web addresses with a neutral pointer: links are only ever shown from the catalog."""
    return URL_RE.sub("[web address in the manual; not shown because it is not verified]", text)
