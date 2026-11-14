"""Headless tests for the Larry chat widget (app.py run through Streamlit's AppTest).

Gemini is disabled (blank env vars), so answers are the deterministic "sources only"
or insufficient-evidence responses. CSS positioning can't be checked here; see the
manual browser checklist.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT
from reslink.larry import HISTORY_KEY, LOADING_MESSAGE, OPEN_KEY, WELCOME_MESSAGE

APP = str(PROJECT_ROOT / "app.py")
LOCKOUT_URL = "https://saweb.asa.utk.edu/housing_ra/ra_login.asp"


def start(monkeypatch, catalog_path: Path | None = None) -> AppTest:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "")
    if catalog_path is not None:
        monkeypatch.setenv("RESLINK_CATALOG_PATH", str(catalog_path))
    else:
        monkeypatch.delenv("RESLINK_CATALOG_PATH", raising=False)
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def open_larry(at: AppTest) -> AppTest:
    at.button(key="larry_launch").click().run()
    assert not at.exception, at.exception
    return at


def ask(at: AppTest, question: str) -> AppTest:
    at.chat_input(key="larry_input").set_value(question).run()
    assert not at.exception, at.exception
    return at


def button_keys(at: AppTest) -> set[str]:
    return {b.key for b in at.button}


def all_markdown(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


# --- launcher / open / close -------------------------------------------------------


def test_larry_starts_closed_with_launcher(monkeypatch):
    at = start(monkeypatch)
    assert at.session_state[OPEN_KEY] is False
    assert "larry_launch" in button_keys(at)
    assert at.button(key="larry_launch").label == "Larry"
    assert "larry_close" not in button_keys(at)
    assert len(at.chat_input) == 0  # no chat input on the dashboard itself


def test_launcher_opens_panel_with_header_and_welcome(monkeypatch):
    at = open_larry(start(monkeypatch))
    assert at.session_state[OPEN_KEY] is True
    assert "larry_close" in button_keys(at)
    assert "larry_launch" not in button_keys(at)
    assert "**Larry**" in all_markdown(at) and "ResLink AI Assistant" in all_markdown(at)
    assert WELCOME_MESSAGE in all_markdown(at)
    assert at.chat_input(key="larry_input").placeholder.startswith("Ask Larry a question")


def test_close_button_minimizes_panel(monkeypatch):
    at = open_larry(start(monkeypatch))
    at.button(key="larry_close").click().run()
    assert not at.exception
    assert at.session_state[OPEN_KEY] is False
    assert "larry_launch" in button_keys(at)
    assert len(at.chat_input) == 0


def test_open_close_cycle_is_repeatable(monkeypatch):
    at = start(monkeypatch)
    for _ in range(3):
        open_larry(at)
        assert "larry_close" in button_keys(at)
        at.button(key="larry_close").click().run()
        assert "larry_launch" in button_keys(at)


def test_dashboard_still_renders_while_larry_is_open(monkeypatch):
    at = start(monkeypatch)
    tabs_before = len(at.tabs)
    dashboard_links = len(at.get("link_button"))
    open_larry(at)
    assert len(at.tabs) == tabs_before
    assert len(at.get("link_button")) == dashboard_links


# --- conversation --------------------------------------------------------------------


def test_answer_shows_verified_cards_inside_larry(monkeypatch):
    at = open_larry(start(monkeypatch))
    dashboard_links = len(at.get("link_button"))
    ask(at, "A resident is locked out of their room")
    assert any("isn't configured" in w.value for w in at.warning)  # Gemini disabled in tests
    new_urls = [b.proto.url for b in at.get("link_button")[dashboard_links:]]
    assert new_urls[0] == LOCKOUT_URL
    assert any("sign-in required" in c.value for c in at.caption)
    assert at.session_state[OPEN_KEY] is True  # panel stays open after sending


def test_no_match_is_honest_inside_larry(monkeypatch, tmp_path):
    path = tmp_path / "resources.json"
    path.write_text("[]", encoding="utf-8")
    at = ask(open_larry(start(monkeypatch, path)), "Where do I submit my weekly RA report?")
    assert any("couldn't find a verified resource" in i.value for i in at.info)


def test_multiple_exchanges(monkeypatch):
    at = open_larry(start(monkeypatch))
    questions = ["Where can I see my floor roster?", "What is the quiet hours policy?", "Where can I park overnight?"]
    for q in questions:
        ask(at, q)
    history = at.session_state[HISTORY_KEY]
    assert [q for q, _ in history] == questions
    # welcome + (user + assistant) per exchange
    assert len(at.chat_message) == 1 + 2 * len(questions)


def test_history_survives_minimize_and_reopen(monkeypatch):
    at = open_larry(start(monkeypatch))
    ask(at, "Where can I see my floor roster?")
    ask(at, "What is the guest policy?")
    at.button(key="larry_close").click().run()
    assert len(at.chat_message) == 0  # nothing rendered while closed
    open_larry(at)
    assert [q for q, _ in at.session_state[HISTORY_KEY]] == [
        "Where can I see my floor roster?",
        "What is the guest policy?",
    ]
    assert len(at.chat_message) == 1 + 2 * 2
    user_texts = [m.markdown[0].value for m in at.chat_message if m.name == "user"]
    assert user_texts == ["Where can I see my floor roster?", "What is the guest policy?"]


def test_each_question_is_answered_once(monkeypatch):
    # A rerun without a new submission (e.g. reopening) must not re-ask the last question.
    calls = []
    import reslink.assistant

    real = reslink.assistant.answer_question

    def counting(*args, **kwargs):
        calls.append(args[0])
        return real(*args, **kwargs)

    monkeypatch.setattr(reslink.assistant, "answer_question", counting)
    at = open_larry(start(monkeypatch))
    ask(at, "Where can I see my floor roster?")
    at.button(key="larry_close").click().run()
    open_larry(at)
    at.run()
    assert calls == ["Where can I see my floor roster?"]


def test_loading_message_text():
    assert "Larry" in LOADING_MESSAGE


# --- retrieval mode (Milestone 3) -------------------------------------------------------------


def _sidebar_text(at: AppTest) -> str:
    return "\n".join(m.value for m in at.sidebar.markdown) + "\n".join(c.value for c in at.sidebar.caption)


def test_sidebar_reports_retrieval_mode(monkeypatch):
    at = start(monkeypatch)
    assert "Retrieval:" in _sidebar_text(at)


def test_missing_semantic_index_falls_back_to_keyword(monkeypatch, tmp_path):
    monkeypatch.setenv("RESLINK_CHROMA_PATH", str(tmp_path / "no-chroma-here"))
    at = start(monkeypatch)
    text = _sidebar_text(at)
    assert "Retrieval: keyword only" in text and "not built" in text
    # Larry still answers from keyword retrieval with verified links.
    open_larry(at)
    dashboard_links = len(at.get("link_button"))
    ask(at, "A resident is locked out of their room")
    assert at.get("link_button")[dashboard_links].proto.url == LOCKOUT_URL


# --- Milestone 4: procedures tab and privacy -----------------------------------------------------


def test_dashboard_has_procedures_tab_and_manual_without_link(monkeypatch):
    at = start(monkeypatch)
    assert any(t.label == "Procedures" for t in at.tabs)
    assert any("Front Desk Residence Hall Manual" in m.value for m in at.markdown)
    assert not any("Front Desk" in b.label for b in at.get("link_button"))  # never a link
    assert any("no public link" in c.value for c in at.caption)


def test_personal_info_is_blocked_and_redacted_in_history(monkeypatch):
    at = open_larry(start(monkeypatch))
    ask(at, "Charge John Smith, UT ID 123456789, room 214 for an excessive lockout")
    assert any("personal information" in i.value for i in at.info)
    [(stored, _)] = at.session_state[HISTORY_KEY]
    assert "123456789" not in stored and "[9-digit ID number removed]" in stored
    user_texts = [m.markdown[0].value for m in at.chat_message if m.name == "user"]
    assert all("123456789" not in t for t in user_texts)
