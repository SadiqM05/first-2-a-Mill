"""Procedure (Markdown transcription) parsing, metadata, and the real knowledge base's structure."""

import json
import re

import pytest

from conftest import FIXTURES, PROJECT_ROOT
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH
from reslink.procedures import (
    OVERVIEW_SUFFIX,
    UNVERIFIED_URL_REVIEW,
    ProcedureError,
    load_meta,
    load_procedure_chunks,
    neutralize_urls,
    parse_procedures,
)

SAMPLE = (FIXTURES / "procedures_sample.md").read_text(encoding="utf-8")
REAL_PATH = PROJECT_ROOT / "data" / "procedures" / "residence_hall_front_desk_knowledge_base.md"


def by_section(chunks):
    return {c.section: c for c in chunks}


# --- parsing the fixture ------------------------------------------------------------------


def test_procedures_inherit_group_page_range():
    units = by_section(parse_procedures(SAMPLE, "doc"))
    first = units["First Procedure"]
    assert (first.page, first.page_end, first.group) == (10, 12, "Alpha Group")
    assert units["Second Procedure"].page == 10


def test_group_intro_becomes_overview_unit():
    units = by_section(parse_procedures(SAMPLE, "doc"))
    overview = units["Alpha Group" + OVERVIEW_SUFFIX]
    assert overview.text == "Alpha overview text before any procedure."
    assert (overview.page, overview.page_end) == (10, 12)


def test_group_without_procedures_is_one_unit_with_table():
    beta = by_section(parse_procedures(SAMPLE, "doc"))["Beta Reference"]
    assert (beta.page, beta.page_end) == (7, None)
    assert "| Widgets | PLACEHOLDER widget issues. |" in beta.text
    assert "4. PLACEHOLDER orphan step four." in beta.text


def test_body_is_verbatim_with_nested_steps_and_notes():
    first = by_section(parse_procedures(SAMPLE, "doc"))["First Procedure"]
    expected = (
        "1. PLACEHOLDER step one.\n   - Nested detail for step one.\n"
        "2. PLACEHOLDER step two (up to **99 hours**).\n"
        "3. Go to https://placeholder.example.org/path/.\n"
        "4. PLACEHOLDER step four.\n\n**Manual note:** PLACEHOLDER note that must be kept."
    )
    assert first.text == expected


def test_source_limitation_marks_incomplete():
    units = by_section(parse_procedures(SAMPLE, "doc"))
    assert units["Second Procedure"].incomplete.startswith("The photographed page ends here")
    assert units["First Procedure"].incomplete is None


def test_url_in_body_is_flagged_and_neutralized_for_evidence():
    first = by_section(parse_procedures(SAMPLE, "doc"))["First Procedure"]
    assert UNVERIFIED_URL_REVIEW in first.review
    out = neutralize_urls(first.text)
    assert "http" not in out and "placeholder.example.org" not in out
    assert out.count("[web address in the manual") == 1 and "step four" in out


def test_chunk_indexes_unique_and_ordered():
    chunks = parse_procedures(SAMPLE, "doc")
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize("bad, message", [
    ("## No Pages Here\n\n### P\n1. x\n", "needs a page reference"),
    ("### Orphan\n1. x\n", "outside a valid '##' group"),
    ("## G (p. 1)\n\n### Empty\n\n### Other\n1. x\n", "is empty"),
    ("## G (p. 1)\n\n### Same\n1. x\n\n### Same\n2. y\n", "duplicate section"),
    ("## G (pp. 9–3)\n\n### P\n1. x\n", "ends before it starts"),
    ("Just text, no groups.\n", "no '##' procedure groups"),
])
def test_structural_errors(bad, message):
    with pytest.raises(ProcedureError) as info:
        parse_procedures(bad, "doc")
    assert any(message in e for e in info.value.errors)


def test_meta_validation(tmp_path):
    path = tmp_path / "x.meta.json"
    path.write_text(json.dumps({"related": {"Unknown": ["a"], "Known": ["missing-id"]}, "review": {"Known": ["n"]}}),
                    encoding="utf-8")
    with pytest.raises(ProcedureError) as info:
        load_meta(path, {"Known"}, {"a"})
    joined = " ".join(info.value.errors)
    assert "unknown section 'Unknown'" in joined and "unknown catalog IDs ['missing-id']" in joined


def test_missing_source_file_is_a_warning_not_a_crash(placeholder_catalog_path, tmp_path):
    from reslink.catalog import parse_catalog

    resources = parse_catalog([{"id": "t", "title": "T", "category": "procedures",
                                "content_type": "transcription", "source_path": "nope.md"}])
    chunks, warnings = load_procedure_chunks(resources, tmp_path)
    assert chunks == [] and "source file not found" in warnings[0]


# --- the real knowledge base ------------------------------------------------------------------

REAL_RESOURCES = load_catalog(DEFAULT_CATALOG_PATH)
REAL, REAL_WARNINGS = load_procedure_chunks(REAL_RESOURCES, PROJECT_ROOT)
REAL_BY = by_section(REAL)


def test_real_file_loads_without_warnings():
    assert REAL_WARNINGS == []
    assert len(REAL) == 24  # 18 from pages 18 and 24-32, plus 6 merged from pages 16 and 39
    assert all(c.resource_id == "front-desk-manual" for c in REAL)


@pytest.mark.parametrize("section, pages", [
    ("Steps to Issue Access Card", (24, 26)),
    ("Steps for Recore — Lost Keys or Lockout Keys Never Returned", (27, 29)),
    ("Checking IN Packages", (30, 32)),
    ("Mail & Delivery Processing" + OVERVIEW_SUFFIX, (30, 32)),
    ("School Dude — Problem Type Reference", (18, None)),
])
def test_real_sections_and_pages(section, pages):
    c = REAL_BY[section]
    assert (c.page, c.page_end) == pages


def test_real_markdown_is_preserved_verbatim():
    raw = REAL_PATH.read_text(encoding="utf-8")
    for c in REAL:
        assert c.text in raw, f"{c.section} body is not an exact substring of the source"


def test_real_step_order_and_notes_preserved():
    text = REAL_BY["Checking IN Packages"].text
    numbers = [int(m) for m in re.findall(r"^(\d+)\.", text, flags=re.M)]
    assert numbers == list(range(1, 13))
    assert "RAW" in text and "Skip to step 7" in text
    lost = REAL_BY["Steps for Lost Card"].text
    assert "**Manual note:** Some building headstaff members" in lost
    assert "UT ID # and room #" in lost  # template placeholder kept, never filled


def test_real_incomplete_units():
    incomplete = {c.section for c in REAL if c.incomplete}
    assert incomplete == {"Return to Sender", "School Dude — Problem Type Reference",
                          "Equipment Checkout / Check-In", "SchoolDude Maintenance Requests",
                          "Resident Report / Area Coverage Follow-Up (Partial Procedure)"}
    assert "Steps 1–3" in REAL_BY["School Dude — Problem Type Reference"].incomplete


def test_real_review_flags():
    flagged = {c.section for c in REAL if c.review}
    assert {"Excessive Lockouts — Access Cards", "Excessive Lockouts — Keys",
            "Giving Recored Keys to Residents"} <= flagged
    url_flagged = {c.section for c in REAL if UNVERIFIED_URL_REVIEW in c.review}
    assert url_flagged == {"Steps to Issue Access Card", "Steps for Returned Cards", "Steps for Lost Card"}


def test_real_related_links_are_catalog_ids():
    ids = {r.id for r in REAL_RESOURCES}
    assert all(set(c.related) <= ids for c in REAL)
    assert REAL_BY["Steps for Lost Card"].related == ("lockout-card-access", "maintenance-request-portal")
    assert REAL_BY["Checking IN Packages"].related == ()  # SC Logic has no verified catalog link


# --- pages 16 and 39 (merged from the second transcription) -------------------------------------

NEW_UNITS = {
    "Equipment Checkout / Check-In": 16, "Public Room Reservations": 16, "Lobby Advertisements": 16,
    "SchoolDude Maintenance Requests": 16,
    "Resident Report / Area Coverage Follow-Up (Partial Procedure)": 39, "Fire Panel Response": 39,
}


@pytest.mark.parametrize("section, page", NEW_UNITS.items())
def test_new_units_present_with_page(section, page):
    c = REAL_BY[section]
    assert (c.page, c.page_end) == (page, None)
    assert f"**Source:** p. {page}" in c.text  # original source line preserved


def test_new_units_keep_original_notes_and_subheadings():
    assert "> **Incomplete procedure:** The remaining work-order submission steps" in REAL_BY["SchoolDude Maintenance Requests"].text
    assert "> **Note:** The beginning of this procedure is not visible" in REAL_BY[
        "Resident Report / Area Coverage Follow-Up (Partial Procedure)"].text
    assert "**When Area Coverage Arrives**" in REAL_BY[
        "Resident Report / Area Coverage Follow-Up (Partial Procedure)"].text
    assert "**Front Desk Procedure**" in REAL_BY["Public Room Reservations"].text


def test_fire_panel_is_safety_critical_and_complete_text_kept():
    fire = REAL_BY["Fire Panel Response"]
    assert fire.safety and "emergency responders" in fire.safety and "does not give fire-panel operating steps" in fire.safety
    assert "> **Important:** This section reproduces the pictured manual's instructions" in fire.text
    assert fire.review == ()  # the safety notice covers it; no "transcription issue" label
    assert sum(1 for c in REAL if c.safety) == 1


def test_schooldude_pages_cross_referenced():
    p16, p18 = REAL_BY["SchoolDude Maintenance Requests"], REAL_BY["School Dude — Problem Type Reference"]
    assert any("Steps 2–3 are missing" in r for r in p16.review)
    assert any("SchoolDude Maintenance Requests" in r for r in p18.review)
    assert p16.related == ("maintenance-request-portal",)


def test_no_new_links_invented():
    ids = {r.id for r in REAL_RESOURCES}
    for section in NEW_UNITS:
        assert set(REAL_BY[section].related) <= ids
    assert REAL_BY["Public Room Reservations"].related == ()  # 25Live has no verified catalog link
