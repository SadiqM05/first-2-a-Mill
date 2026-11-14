"""Procedures end to end (offline): retrieval of whole units, citations, caveats, related links,
privacy blocking, and the keyword-only fallback. Gemini is replaced by a fake generator."""

import json
import re

import pytest

from conftest import PROJECT_ROOT
from reslink.assistant import CAVEAT_INCOMPLETE, SYSTEM_INSTRUCTION, answer_question
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_INDEX_PATH
from reslink.ingest import load_chunks
from reslink.models import Citation, Status
from reslink.privacy import detect_personal_info, redact
from reslink.retrieval import HybridRetriever, KeywordRetriever

RESOURCES = load_catalog(DEFAULT_CATALOG_PATH)
CHUNKS, _ = load_chunks(DEFAULT_INDEX_PATH, RESOURCES, PROJECT_ROOT)
KEYWORD = KeywordRetriever(RESOURCES, CHUNKS)
MANUAL = "front-desk-manual"
CHECK_IN = f"{MANUAL}#checking-in-packages"
LOST_CARD = f"{MANUAL}#steps-for-lost-card"
RTS = f"{MANUAL}#return-to-sender"


class FakeGenerator:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def generate(self, system_instruction, prompt, schema):
        self.calls.append(prompt)
        return json.dumps(self.output)


def ok(answer, *cited):
    return {"sufficient": True, "answer": answer, "cited_ids": list(cited)}


def doc_evidence(question, retriever=KEYWORD):
    return {e.evidence_id: e for e in retriever.retrieve(question) if e.source == "document"}


# --- retrieval ---------------------------------------------------------------------------------


def test_procedure_is_retrieved_whole_never_truncated():
    e = doc_evidence("How do I check in a package?")[CHECK_IN]
    source = next(c for c in CHUNKS if c.section == "Checking IN Packages")
    assert source.text in e.text  # complete body, verbatim
    numbers = [int(n) for n in re.findall(r"^(\d+)\.", e.text, flags=re.M)]
    assert numbers == list(range(1, 13))


def test_procedure_evidence_header_states_section_pages_and_status():
    e = doc_evidence("How do I check in a package?")[CHECK_IN]
    first, second = e.text.splitlines()[:2]
    assert first == "Source: Front Desk Residence Hall Manual, § Checking IN Packages, pp. 30–32 (group: Mail & Delivery Processing)"
    assert "not independently verified as current" in second
    assert (e.section, e.page, e.page_end) == ("Checking IN Packages", 30, 32)


def test_unverified_url_never_reaches_the_model():
    e = doc_evidence("What do I do for a lost temporary access card?")[LOST_CARD]
    assert "housing.utk.edu" not in e.text and "http" not in e.text
    assert "FLAGGED FOR REVIEW" in e.text


def rts_evidence():
    # Built directly (keyword ranking for this wording is a documented miss; ranking isn't under test).
    chunk = next(c for c in CHUNKS if c.section == "Return to Sender")
    return KEYWORD.page_evidence([chunk], 1.0)


class FixedRetriever:
    def __init__(self, evidence):
        self.evidence = evidence

    def retrieve(self, query, top_k=3):
        return list(self.evidence)


def test_incomplete_source_is_stated_in_evidence():
    e = rts_evidence()
    assert e.evidence_id == RTS
    assert "INCOMPLETE SOURCE: The photographed page ends" in e.text


def test_pdf_evidence_unchanged():
    e = doc_evidence("What is the minimum GPA for RAs?")["ra-job-description@p5"]
    assert e.text.startswith("Source: Resident Assistant Job Description (Residence Life Manual), page 5\n")
    assert e.section is None and e.evidence_id == "ra-job-description@p5"


def test_keyword_only_fallback_serves_procedures():
    hybrid = HybridRetriever(KEYWORD, None)
    ids = [e.evidence_id for e in hybrid.retrieve("How do I check in a package?")]
    assert CHECK_IN in ids and hybrid.last_mode == "keyword"


# --- citations, caveats, related links ------------------------------------------------------------


def test_section_citation_label_and_no_link():
    manual = next(r for r in RESOURCES if r.id == MANUAL)
    c = Citation(manual, page=30, section="Checking IN Packages", page_end=32)
    assert c.label == "Front Desk Residence Hall Manual, § Checking IN Packages, pp. 30–32"
    assert c.link is None


def test_grounded_procedure_answer_has_citation_unverified_caveat_and_no_link():
    gen = FakeGenerator(ok("1. Log in to SC Logic...", CHECK_IN))
    r = answer_question("How do I check in a package?", KEYWORD, gen)
    assert r.status is Status.GROUNDED
    [c] = r.citations
    assert c.label.endswith("§ Checking IN Packages, pp. 30–32") and c.link is None
    assert any("not independently verified as current" in x for x in r.caveats)


def test_related_portal_links_come_from_catalog_ids():
    gen = FakeGenerator(ok("Mark the card lost...", LOST_CARD))
    r = answer_question("What do I do for a lost temporary access card?", KEYWORD, gen)
    ids = [x.id for x in r.resources]
    assert ids[0] == MANUAL
    assert "lockout-card-access" in ids and "maintenance-request-portal" in ids
    urls = {x.url for x in r.resources if x.url}
    assert "https://saweb.asa.utk.edu/housing_ra/ra_login.asp" in urls
    assert not any("housing.utk.edu" in u for u in urls)  # unverified URL never becomes a link
    assert any("Flagged for review" in x and "web address" in x for x in r.caveats)


def test_incomplete_caveat_added_by_code():
    gen = FakeGenerator(ok("Stamp RTS...", RTS))
    r = answer_question("How do I return mail to sender?", FixedRetriever([rts_evidence()]), gen)
    expected = CAVEAT_INCOMPLETE.format(section="Return to Sender", text="")
    assert any(x.startswith(expected) for x in r.caveats)


def test_no_caveats_for_pdf_answers():
    gen = FakeGenerator(ok("2.75 cumulative.", "ra-job-description@p5"))
    r = answer_question("What is the minimum GPA for RAs?", KEYWORD, gen)
    assert r.caveats == () and r.citations[0].link.endswith("#page=5")


def test_invented_section_citation_is_dropped():
    gen = FakeGenerator(ok("Made up.", f"{MANUAL}#refund-procedure"))
    r = answer_question("How do I check in a package?", KEYWORD, gen)
    assert r.status is Status.INSUFFICIENT_EVIDENCE and r.citations == ()


def test_prompt_rules_for_procedures_present():
    text = " ".join(SYSTEM_INSTRUCTION.split())
    for phrase in ["give every documented step in the original order", "answer only that",
                   "Never invent missing steps, fees", "INCOMPLETE SOURCE",
                   "placeholders exactly", "Never ask the user for"]:
        assert phrase in text


# --- privacy ----------------------------------------------------------------------------------


@pytest.mark.parametrize("text, kind", [
    ("Charge John Smith, UT ID 123456789, room 214", "a 9-digit ID number"),
    ("email jsmith3@vols.utk.edu about it", "an email address"),
    ("call her at (865) 555-0142", "a phone number"),
    ("call 865-555-0142", "a phone number"),
    ("ssn 123-45-6789", "an SSN-like number"),
])
def test_privacy_detects_obvious_patterns(text, kind):
    assert kind in detect_personal_info(text)


@pytest.mark.parametrize("text", [
    "How do I check in a package?",
    "A resident in room 214 is locked out",  # room numbers alone are allowed
    "Lockout cards are up to 72 hours",
    "The PIK number starts with 888",
])
def test_privacy_allows_normal_questions(text):
    assert detect_personal_info(text) == []


def test_privacy_block_skips_retrieval_and_gemini():
    class Boom:
        def retrieve(self, *a, **k):
            raise AssertionError("retrieval must not run")

    gen = FakeGenerator(ok("x"))
    r = answer_question("Charge John Smith, UT ID 123456789, room 214 for a lockout", Boom(), gen)
    assert r.status is Status.INSUFFICIENT_EVIDENCE and "personal information" in r.notice
    assert "9-digit ID number" in r.notice and "only catches obvious patterns" in r.notice
    assert gen.calls == []


def test_redact():
    assert redact("UT ID 123456789 or jsmith3@vols.utk.edu") == "UT ID [9-digit ID number removed] or [email address removed]"


# --- step formatting (formatting only, never content) -------------------------------------------

from reslink.assistant import format_steps  # noqa: E402

INLINE = ("Follow these steps: 1. Log in. 2. Scan package. - If assigned, skip to step 4. "
          "- If NOT assigned, proceed to step 3. 3. Find student. 4. Click submit.")


def test_inline_steps_become_lines_without_changing_words():
    out = format_steps(INLINE)
    assert out.split() == INLINE.split()
    assert out.splitlines()[2:] == [
        "1. Log in.", "2. Scan package.", "   - If assigned, skip to step 4.",
        "   - If NOT assigned, proceed to step 3.", "3. Find student.", "4. Click submit.",
    ]


@pytest.mark.parametrize("text", [
    "1. Already\n2. A proper\n3. List",                       # already formatted
    "RAs earn $1,200. Paid monthly. See page 6.",              # prose with numbers
    "Do step 1. Then 2. Done.",                                # fewer than 3 inline steps
    "Up to 72 hours. 2 hours if the phone is in the room.",    # numbers that aren't steps
])
def test_formatter_leaves_other_text_alone(text):
    assert format_steps(text) == text


def test_grounded_answer_is_formatted():
    gen = FakeGenerator(ok(INLINE, CHECK_IN))
    r = answer_question("How do I check in a package?", KEYWORD, gen)
    assert "\n1. Log in." in r.answer and "\n4. Click submit." in r.answer
