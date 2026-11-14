"""Partial (incomplete) procedures: qualified answers, original step numbers, gap marking,
companion fragments, declines, and safety protection. Offline; Gemini replaced by a fake."""

import json
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT
from reslink.assistant import (
    NOTICE_PARTIAL_PROCEDURE,
    NOTICE_NO_MATCH,
    SAFETY_FALLBACK,
    SYSTEM_INSTRUCTION,
    answer_question,
    mark_step_gaps,
)
from reslink.catalog import load_catalog
from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_INDEX_PATH
from reslink.ingest import load_chunks
from reslink.models import Status
from reslink.retrieval import KeywordRetriever

RESOURCES = load_catalog(DEFAULT_CATALOG_PATH)
CHUNKS, _ = load_chunks(DEFAULT_INDEX_PATH, RESOURCES, PROJECT_ROOT)
KEYWORD = KeywordRetriever(RESOURCES, CHUNKS)
M = "front-desk-manual#"
SD16, SD18 = M + "schooldude-maintenance-requests", M + "school-dude-problem-type-reference"
SD_Q = "How do I enter a SchoolDude work order?"
SD_ANSWER = ("The work-order steps are only partly documented.\n"
             "1. Click the “New Work Order” tab at the top.\n"
             "4. Please select NO to indicate that you will not complete this work.\n"
             "5. Press Submit.")


class FakeGenerator:
    def __init__(self, output):
        self.output, self.prompts = output, []

    def generate(self, system_instruction, prompt, schema):
        self.prompts.append(prompt)
        return json.dumps(self.output)


class FixedRetriever:
    def __init__(self, evidence):
        self.evidence = evidence

    def retrieve(self, query, top_k=3):
        return list(self.evidence)


def out(answer, *cited, sufficient=True, partial=None):
    data = {"sufficient": sufficient, "answer": answer, "cited_ids": list(cited)}
    if partial is not None:
        data["partial"] = partial
    return data


def top_level_numbers(text):
    import re

    return [int(n) for n in re.findall(r"^(\d+)\.\s", text, flags=re.M)]


# --- step-gap marking (formatting only) -----------------------------------------------------------


def test_gap_in_contiguous_list_is_marked_and_numbers_kept():
    text, gaps = mark_step_gaps("Intro.\n1. First.\n4. Fourth.\n5. Fifth.")
    assert gaps
    assert top_level_numbers(text) == [1, 4, 5]
    assert "*Steps 2–3 are missing from the source.*" in text
    assert text.index("1. First.") < text.index("Steps 2–3") < text.index("4. Fourth.")


def test_single_missing_step_and_leading_gap():
    text, _ = mark_step_gaps("1. a\n3. c")
    assert "*Step 2 is missing from the source.*" in text
    text, gaps = mark_step_gaps("Only the end is documented:\n4. Select NO.\n5. Submit.")
    assert gaps and "*Steps 1–3 are missing from the source.*" in text and top_level_numbers(text) == [4, 5]


def test_sub_bullets_and_blank_lines_do_not_break_detection():
    text, gaps = mark_step_gaps("1. a\n   - detail\n\n4. d")
    assert gaps and "Steps 2–3" in text


@pytest.mark.parametrize("text", [
    "1. a\n2. b\n3. c",                                   # complete procedure
    "1. a\n   - x\n2. b",                                 # sub-bullets
    "No list here, just 4. a number mid-sentence.",       # prose
    "Intro:\n1. a\n2. b\nThat's all.",                    # no gap: text left exactly as written
])
def test_no_insertion_needed(text):
    assert mark_step_gaps(text) == (text, False)


def test_model_marked_gap_is_kept_and_separated():
    # Without blank lines Markdown would fold the gap line into step 1 and render "4." as "2.".
    text, gaps = mark_step_gaps("1. a\nSteps 2–3 are missing from the source.\n4. d")
    assert gaps and text == "1. a\n\nSteps 2–3 are missing from the source.\n\n4. d"
    assert text.count("missing") == 1  # no duplicate gap line


def test_live_inline_partial_answer_is_listed_with_original_numbers():
    from reslink.assistant import format_steps

    live = ("These instructions are incomplete because steps 2–3 are missing from the source; check "
            "current official documentation or ask headstaff. 1. Click the ‘New Work Order’ tab at the top. "
            "Steps 2–3 are missing from the source. 4. Please select NO to indicate that you will not "
            "complete this work. 5. Press Submit.")
    text, gaps = mark_step_gaps(format_steps(live))
    assert gaps and top_level_numbers(text) == [1, 4, 5]
    assert "\n\n1. Click the ‘New Work Order’ tab at the top.\n\nSteps 2–3 are missing from the source.\n\n4. Please" in text


def test_inline_jump_without_missing_statement_is_not_listed():
    from reslink.assistant import format_steps

    assert format_steps("Call 1. a 4. b 5. c") == "Call 1. a 4. b 5. c"


def test_inline_steps_starting_the_answer_are_split():
    # Live Return to Sender answer shape: "1." at the very start, the rest inline.
    from reslink.assistant import format_steps

    text = format_steps("1. Return it. 2. Mark the address out. 3. Stamp RTS. - Circle NAA if needed.")
    assert text == "1. Return it.\n2. Mark the address out.\n3. Stamp RTS.\n   - Circle NAA if needed."


# --- companions: fragments retrieved together, never merged ------------------------------------------


def test_fragment_evidence_names_its_companion():
    by_id = {e.evidence_id: e for e in KEYWORD.retrieve(SD_Q)}
    assert "OTHER FRAGMENT OF THE SAME PROCEDURE: § School Dude — Problem Type Reference" in by_id[SD16].text
    assert "OTHER FRAGMENT OF THE SAME PROCEDURE: § SchoolDude Maintenance Requests" in by_id[SD18].text
    assert "original numbers" in by_id[SD16].text


def test_schooldude_fragments_retrieved_together():
    ids = [e.evidence_id for e in KEYWORD.retrieve(SD_Q)]
    assert SD16 in ids and SD18 in ids
    sd16 = next(e for e in KEYWORD.retrieve(SD_Q) if e.evidence_id == SD16)
    assert "1. Click the **“New Work Order”** tab" in sd16.text and "Press **Submit**" not in sd16.text


def test_companion_added_from_the_other_side_too():
    ids = [e.evidence_id for e in KEYWORD.retrieve("Which School Dude problem type should I use for bed bugs?")]
    assert SD18 in ids and SD16 in ids


# --- partial answers -------------------------------------------------------------------------------


def test_partial_schooldude_answer_is_useful_and_qualified():
    r = answer_question(SD_Q, KEYWORD, FakeGenerator(out(SD_ANSWER, SD16, SD18, partial=True)))
    assert r.status is Status.PARTIAL and r.notice == NOTICE_PARTIAL_PROCEDURE
    assert top_level_numbers(r.answer) == [1, 4, 5]  # original numbering, not renumbered
    assert "Steps 2–3 are missing from the source." in r.answer
    labels = [c.label for c in r.citations]
    assert labels == ["Front Desk Residence Hall Manual, § SchoolDude Maintenance Requests, p. 16",
                      "Front Desk Residence Hall Manual, § School Dude — Problem Type Reference, p. 18"]
    assert [x.id for x in r.resources if x.url] == ["maintenance-request-portal"]
    kinds = [n.kind for n in r.caveats]
    assert kinds.count("incomplete") == 2 and "review" in kinds


def test_gap_alone_marks_partial_when_source_is_incomplete():
    r = answer_question(SD_Q, KEYWORD, FakeGenerator(out(SD_ANSWER, SD16, SD18)))  # no partial flag
    assert r.status is Status.PARTIAL


def test_partial_flag_without_incomplete_source_stays_grounded():
    r = answer_question("How do I check in a package?", KEYWORD,
                        FakeGenerator(out("1. Log in to SC Logic.\n2. Click Check In.", M + "checking-in-packages", partial=True)))
    assert r.status is Status.GROUNDED and r.notice is None


def test_incomplete_source_but_fully_answered_question_stays_grounded():
    r = answer_question("Which School Dude problem type should I use for bed bugs?", KEYWORD,
                        FakeGenerator(out("Use Pest Control.", SD18, partial=False)))
    assert r.status is Status.GROUNDED and r.notice is None
    assert any(n.kind == "incomplete" for n in r.caveats)  # the source note is still shown


def test_complete_procedure_unaffected():
    steps = "\n".join(f"{i}. Step {i}." for i in range(1, 13))
    r = answer_question("How do I check in a package?", KEYWORD, FakeGenerator(out(steps, M + "checking-in-packages", partial=False)))
    assert r.status is Status.GROUNDED and r.notice is None
    assert r.answer == steps and "missing" not in r.answer


# --- declines ------------------------------------------------------------------------------------------


def test_request_for_missing_steps_is_declined():
    gen = FakeGenerator(out("Steps 2 and 3 aren't in ResLink's verified sources.", sufficient=False, partial=True))
    r = answer_question("What are steps 2 and 3 for submitting a SchoolDude work order?", KEYWORD, gen)
    assert r.status is Status.INSUFFICIENT_EVIDENCE and r.citations == ()
    assert r.notice != NOTICE_PARTIAL_PROCEDURE


def test_undocumented_procedure_declined_without_model_call():
    gen = FakeGenerator(out("x"))
    r = answer_question("How do I process a vending machine refund in Banner?", FixedRetriever([]), gen)
    assert r.status is Status.INSUFFICIENT_EVIDENCE and r.notice == NOTICE_NO_MATCH and gen.prompts == []


def test_invented_citation_to_missing_steps_is_dropped():
    r = answer_question(SD_Q, KEYWORD, FakeGenerator(out("2. Fill out the top.", M + "schooldude-step-2", partial=True)))
    assert r.status is Status.INSUFFICIENT_EVIDENCE and r.answer is None


# --- safety stays protected --------------------------------------------------------------------------


def _fire_evidence(incomplete=None):
    e = next(x for x in KEYWORD.retrieve("The fire panel is going off") if x.evidence_id == M + "fire-panel-response")
    return replace(e, incomplete=incomplete) if incomplete else e


def test_safety_guard_runs_before_partial_logic():
    fire = _fire_evidence(incomplete="Hypothetical: later steps missing.")  # incomplete AND safety-critical
    gen = FakeGenerator(out("1. Press acknowledge.\n3. Press silence.", fire.evidence_id, partial=True))
    r = answer_question("The fire panel is going off", FixedRetriever([fire]), gen)
    assert r.answer == SAFETY_FALLBACK
    assert r.status is Status.GROUNDED and r.notice is None  # never presented as "documented steps"
    assert r.caveats[0].kind == "safety"


def test_prompt_rules_for_partial_procedures():
    text = " ".join(SYSTEM_INSTRUCTION.split())
    for phrase in ["set sufficient to true and partial to true", "ORIGINAL step numbers (never renumber",
                   "Steps 2–3 are missing from the source.", "check current official documentation or ask headstaff",
                   "Never fill a gap or imply missing steps are optional", "do not present them as one complete procedure",
                   "Do NOT give fire-panel operating steps"]:
        assert phrase in text, phrase


# --- UI -----------------------------------------------------------------------------------------------


def _render(response):
    from reslink.ui import render_response

    render_response(response)


def test_partial_response_renders_warning_then_numbered_steps():
    r = answer_question(SD_Q, KEYWORD, FakeGenerator(out(SD_ANSWER, SD16, SD18, partial=True)))
    at = AppTest.from_function(_render, args=(r,), default_timeout=30)
    at.run()
    assert not at.exception
    assert at.warning[0].value.startswith("Incomplete procedure:")
    assert any("Steps 2–3 are missing from the source." in m.value for m in at.markdown)
    assert any(c.value.startswith("Sources: ") for c in at.caption)
    assert any(c.value == "Verified links" for c in at.caption)
