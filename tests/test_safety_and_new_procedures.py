"""Pages 16/39 merge: safety-critical handling (fire panel), incomplete-procedure notices, and
retrieval of the new topics. Offline; Gemini is replaced by a fake generator."""

import json

import pytest
from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT
from reslink.assistant import SAFETY_FALLBACK, SYSTEM_INSTRUCTION, answer_question
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_CHROMA_PATH, DEFAULT_INDEX_PATH
from reslink.ingest import load_chunks
from reslink.models import Status
from reslink.retrieval import HybridRetriever, KeywordRetriever
from reslink.semantic import CATALOG_MAX_DISTANCE, DEFAULT_MAX_DISTANCE, SemanticIndex

RESOURCES = load_catalog(DEFAULT_CATALOG_PATH)
CHUNKS, _ = load_chunks(DEFAULT_INDEX_PATH, RESOURCES, PROJECT_ROOT)
KEYWORD = KeywordRetriever(RESOURCES, CHUNKS)
SEMANTIC, STATUS = SemanticIndex.open(DEFAULT_CHROMA_PATH, RESOURCES, CHUNKS)
M = "front-desk-manual#"
FIRE = M + "fire-panel-response"
FIRE_Q = "The fire panel is going off, what do I do?"
PANEL_WORDS = ("acknowledge", "silence", "reset")


class FakeGenerator:
    def __init__(self, output):
        self.output, self.prompts = output, []

    def generate(self, system_instruction, prompt, schema):
        self.prompts.append(prompt)
        return json.dumps(self.output)


def ok(answer, *cited, sufficient=True):
    return {"sufficient": sufficient, "answer": answer, "cited_ids": list(cited)}


# --- retrieval of the new topics -------------------------------------------------------------------

NEW_TOPIC_QUESTIONS = [
    ("What do I do when area coverage arrives for a resident report?", "resident-report-area-coverage-follow-up-partial-procedure"),
    (FIRE_Q, "fire-panel-response"),
    ("What do I do if the fire alarm goes off at the front desk?", "fire-panel-response"),
    ("Can residents check out a vacuum from the front desk?", "equipment-checkout-check-in"),
    ("How do I reserve a public room?", "public-room-reservations"),
    ("Can a restaurant put a flyer in the lobby?", "lobby-advertisements"),
    ("Can someone put flyers in student mailboxes?", "lobby-advertisements"),
    ("How do I enter a SchoolDude work order?", "schooldude-maintenance-requests"),
]


@pytest.mark.parametrize("question, slug", NEW_TOPIC_QUESTIONS)
def test_new_topics_retrieved_by_keyword(question, slug):
    ids = [e.evidence_id for e in KEYWORD.retrieve_documents(question)]
    assert M + slug in ids


@pytest.mark.skipif(SEMANTIC is None, reason=f"semantic index unavailable: {STATUS}")
@pytest.mark.parametrize("question, slug", NEW_TOPIC_QUESTIONS)
def test_new_topics_rank_first_in_hybrid(question, slug):
    hybrid = HybridRetriever(KEYWORD, SEMANTIC, max_distance=DEFAULT_MAX_DISTANCE, catalog_max_distance=CATALOG_MAX_DISTANCE)
    docs = [e.evidence_id for e in hybrid.retrieve(question) if e.source == "document"]
    assert docs[0] == M + slug


def test_new_procedure_citations_have_page_labels():
    r = answer_question("Can someone put flyers in student mailboxes?", KEYWORD,
                        FakeGenerator(ok("Direct them to the Director of Residence Life.", M + "lobby-advertisements")))
    [c] = r.citations
    assert c.label == "Front Desk Residence Hall Manual, § Lobby Advertisements, p. 16" and c.link is None


# --- safety-critical: fire panel ---------------------------------------------------------------------


def test_fire_evidence_is_marked_safety_critical():
    e = next(x for x in KEYWORD.retrieve(FIRE_Q) if x.evidence_id == FIRE)
    assert e.safety and "SAFETY-CRITICAL: Emergency:" in e.text.splitlines()[1]


def test_prompt_rule_forbids_panel_operating_steps():
    text = " ".join(SYSTEM_INSTRUCTION.split())
    assert "Do NOT give fire-panel operating steps" in text and "SAFETY-CRITICAL" in text
    assert "Never suggest treating an unverified alarm as a nuisance alarm" in text


@pytest.mark.parametrize("bad_answer", [
    "1. Press the acknowledge button within 15 seconds.\n2. Have someone investigate.",
    "If it's a nuisance alarm, press silence and then reset.",
    "Silencing the panel is fine once the investigator confirms.",
])
def test_panel_operating_answers_are_replaced(bad_answer):
    r = answer_question(FIRE_Q, KEYWORD, FakeGenerator(ok(bad_answer, FIRE)))
    assert r.answer == SAFETY_FALLBACK
    assert r.caveats[0].kind == "safety" and r.caveats[0].prominent


def test_safety_fallback_is_escalation_only_and_source_based():
    lowered = SAFETY_FALLBACK.lower()
    assert not any(w in lowered.split() for w in PANEL_WORDS)
    for phrase in ["current fire procedures", "emergency responders", "general alarm", "pull station",
                   "fire department", "utpd", "never treat an unverified alarm as a nuisance alarm"]:
        assert phrase in lowered


def test_escalation_answer_is_kept_and_safety_notice_comes_first():
    good = ("Treat it as a real alarm: follow your building's fire procedures and get trained staff to investigate. "
            "If there is any evidence of fire, the Fire Department must respond.")
    r = answer_question(FIRE_Q, KEYWORD, FakeGenerator(ok(good, FIRE)))
    assert r.status is Status.GROUNDED and r.answer.startswith("Treat it as a real alarm")
    assert [n.kind for n in r.caveats][0] == "safety"


def test_declined_fire_answer_still_shows_safety_and_never_panel_steps():
    r = answer_question(FIRE_Q, KEYWORD, FakeGenerator(ok("Press acknowledge; I can't verify more.", sufficient=False)))
    assert r.status is Status.INSUFFICIENT_EVIDENCE
    assert r.answer == SAFETY_FALLBACK
    assert any(n.kind == "safety" for n in r.caveats)


def test_reset_word_in_non_safety_answers_is_untouched():
    r = answer_question("What is the quiet hours policy?", KEYWORD,
                        FakeGenerator(ok("Quiet hours reset each night at 9 p.m.", "housing-policies@p5")))
    assert r.answer == "Quiet hours reset each night at 9 p.m." and not any(n.kind == "safety" for n in r.caveats)


def _render(response):
    from reslink.ui import render_response

    render_response(response)


def test_safety_notice_renders_above_the_answer():
    r = answer_question(FIRE_Q, KEYWORD, FakeGenerator(ok("Follow your building's fire procedures.", FIRE)))
    at = AppTest.from_function(_render, args=(r,), default_timeout=30)
    at.run()
    assert not at.exception
    order = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            if getattr(child, "type", "") in ("error", "markdown", "warning"):
                order.append((child.type, getattr(child, "value", "")))
            walk(child)

    walk(at.main)
    assert order[0][0] == "error" and order[0][1].startswith("Emergency:")
    assert order[1] == ("markdown", "Follow your building's fire procedures.")
    assert all("Emergency:" not in v for t, v in order if t == "warning")  # not duplicated below


# --- incomplete procedures are identified by code ------------------------------------------------------


@pytest.mark.parametrize("question, slug, fragment", [
    ("How do I check in borrowed equipment?", "equipment-checkout-check-in", "does not specify check-in steps"),
    ("How do I enter a SchoolDude work order?", "schooldude-maintenance-requests", "Page 16 ends after the first"),
    ("What do I do when area coverage arrives for a resident report?",
     "resident-report-area-coverage-follow-up-partial-procedure", "Page 39 starts mid-procedure"),
])
def test_incomplete_new_procedures_get_prominent_notice(question, slug, fragment):
    r = answer_question(question, KEYWORD, FakeGenerator(ok("Answer.", M + slug)))
    incomplete = [n for n in r.caveats if n.kind == "incomplete"]
    assert incomplete and fragment in incomplete[0].text and incomplete[0].prominent


def test_schooldude_cross_reference_flag_is_shown():
    r = answer_question("How do I enter a SchoolDude work order?", KEYWORD,
                        FakeGenerator(ok("Click New Work Order.", M + "schooldude-maintenance-requests")))
    reviews = [n.text for n in r.caveats if n.kind == "review"]
    assert any("Steps 2–3 are missing from both transcriptions" in t for t in reviews)
    assert [x.id for x in r.resources if x.url] == ["maintenance-request-portal"]
