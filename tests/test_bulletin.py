"""Staff Bulletin: validation, search, filtering, ordering, empty states, UI integration,
and separation from Larry / the AI retrieval pipeline. Offline; no Gemini calls."""

import ast
import json
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT
from reslink.bulletin import (
    BULLETIN_CATEGORIES,
    Announcement,
    Bulletin,
    BulletinError,
    filter_by_category,
    load_bulletin,
    order,
    parse_bulletin,
    search,
    select,
)
from reslink.config import DEFAULT_BULLETIN_PATH

APP = str(PROJECT_ROOT / "app.py")


def item(**overrides):
    base = {"id": "t-1", "title": "PLACEHOLDER title", "description": "PLACEHOLDER text",
            "category": "general", "published": "2026-11-01"}
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def errors_for(data) -> list[str]:
    with pytest.raises(BulletinError) as info:
        parse_bulletin(data)
    return info.value.errors


def ann(id, published, pinned=False, category="general", title=None, description="x", due=None):
    return Announcement(id=id, title=title or id, description=description, category=category,
                        published=date.fromisoformat(published), pinned=pinned,
                        due=date.fromisoformat(due) if due else None)


# --- validation ----------------------------------------------------------------------------------


def test_real_demo_file_is_valid_and_labeled():
    b = load_bulletin(DEFAULT_BULLETIN_PATH)
    assert b.demo_data is True and "fictional" in b.notice.lower()
    assert len(b.announcements) == 8
    assert sum(a.pinned for a in b.announcements) == 2
    assert {a.category for a in b.announcements} == set(BULLETIN_CATEGORIES)
    assert all(a.title.startswith("[Demo]") for a in b.announcements)


def test_valid_entry_parses_with_defaults():
    [a] = parse_bulletin({"announcements": [item()]}).announcements
    assert (a.pinned, a.due, a.published) == (False, None, date(2026, 11, 1))
    assert a.category_label == "General"


def test_optional_due_date():
    [a] = parse_bulletin({"announcements": [item(due="2026-12-05")]}).announcements
    assert a.due == date(2026, 12, 5)


@pytest.mark.parametrize("bad", ["2026-13-01", "12/05/2026", "20261205", "2026-12-05T09:00", "", 20261205, None])
def test_invalid_due_date(bad):
    data = {"announcements": [{**item(), "due": bad}]}
    assert any("'due' must be a date in YYYY-MM-DD" in e for e in errors_for(data))


@pytest.mark.parametrize("bad", ["2026-02-30", "Nov 1 2026", "2026-11-1"])
def test_invalid_published_date(bad):
    assert any("'published' must be a date" in e for e in errors_for({"announcements": [item(published=bad)]}))


@pytest.mark.parametrize("field", ["id", "title", "description", "category", "published"])
def test_required_fields(field):
    assert any(f"'{field}' is required" in e for e in errors_for({"announcements": [item(**{field: None})]}))


def test_unknown_category_field_and_pinned_type():
    errors = errors_for({"announcements": [item(category="sports", author="x", pinned="yes")]})
    joined = " ".join(errors)
    assert "category 'sports'" in joined and "unknown field(s) ['author']" in joined and "'pinned' must be true or false" in joined


def test_duplicate_ids_and_top_level_shape():
    assert any("duplicate id" in e for e in errors_for({"announcements": [item(), item(title="Other")]}))
    assert "JSON object" in errors_for([item()])[0]
    assert any("'announcements' is required" in e for e in errors_for({"demo_data": True}))
    assert any("unknown top-level" in e for e in errors_for({"announcements": [], "extra": 1}))
    assert any("'demo_data' must be true or false" in e for e in errors_for({"announcements": [], "demo_data": "yes"}))


def test_all_errors_reported_together():
    assert len(errors_for({"announcements": [item(category="x"), item(id="t-2", published="bad")]})) == 2


def test_missing_file_is_not_an_error(tmp_path):
    b = load_bulletin(tmp_path / "nope.json")
    assert b.source_missing and b.announcements == ()


def test_invalid_json_file(tmp_path):
    path = tmp_path / "bulletins.json"
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(BulletinError, match="not valid JSON"):
        load_bulletin(path)


# --- search / filter / order ----------------------------------------------------------------------

ITEMS = [
    ann("a", "2026-11-01", title="Staff meeting moved", description="Thursday in the lounge", category="meetings"),
    ann("b", "2026-11-05", title="Program proposals", description="Submit your December idea", category="programming"),
    ann("c", "2026-11-03", title="Checklist due", description="Return it to the front desk", category="deadlines",
        pinned=True, due="2026-11-02"),
    ann("d", "2026-11-04", title="Supply restock", description="Markers and tape", category="general"),
]


def test_search_title_description_case_and_all_words():
    assert [a.id for a in search(ITEMS, "MEETING")] == ["a"]
    assert [a.id for a in search(ITEMS, "front desk")] == ["c"]  # description, both words
    assert [a.id for a in search(ITEMS, "desk proposals")] == []  # words must all match one item
    assert search(ITEMS, "   ") == ITEMS


def test_category_filter():
    assert [a.id for a in filter_by_category(ITEMS, ["meetings", "general"])] == ["a", "d"]
    assert filter_by_category(ITEMS, []) == ITEMS and filter_by_category(ITEMS, None) == ITEMS


def test_pinned_first_then_newest_first_and_due_not_used():
    # "c" is pinned with the oldest due date; regular items sort by published only.
    assert [a.id for a in order(ITEMS)] == ["c", "b", "d", "a"]


def test_order_ties_are_deterministic():
    tied = [ann("z", "2026-11-01", title="Beta"), ann("y", "2026-11-01", title="alpha")]
    assert [a.id for a in order(tied)] == ["y", "z"]


def test_pinned_items_also_sorted_newest_first():
    pins = [ann("old", "2026-10-01", pinned=True), ann("new", "2026-11-01", pinned=True), ann("reg", "2026-12-01")]
    assert [a.id for a in order(pins)] == ["new", "old", "reg"]


def test_select_combines_and_empty_result():
    b = Bulletin(tuple(ITEMS))
    assert [a.id for a in select(b, "the", ["meetings", "deadlines"])] == ["c", "a"]
    assert select(b, "nothing matches this", ()) == []


# --- separation from Larry / the AI pipeline ---------------------------------------------------------

AI_MODULES = ["retrieval", "semantic", "assistant", "ingest", "procedures", "catalog", "larry", "privacy"]


@pytest.mark.parametrize("module", AI_MODULES)
def test_ai_modules_never_import_bulletin(module):
    tree = ast.parse((PROJECT_ROOT / "reslink" / f"{module}.py").read_text(encoding="utf-8"))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert "reslink.bulletin" not in imported


def test_bulletin_module_has_no_ui_or_ai_imports():
    tree = ast.parse((PROJECT_ROOT / "reslink" / "bulletin.py").read_text(encoding="utf-8"))
    imported = {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    imported |= {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not imported & {"streamlit", "google", "chromadb", "reslink"}


def test_bulletin_text_is_not_in_any_retrieval_source():
    from reslink.catalog import load_catalog
    from reslink.config import DEFAULT_CATALOG_PATH, DEFAULT_INDEX_PATH
    from reslink.ingest import load_chunks
    from reslink.retrieval import KeywordRetriever
    from reslink.semantic import build_documents

    resources = load_catalog(DEFAULT_CATALOG_PATH)
    chunks, _ = load_chunks(DEFAULT_INDEX_PATH, resources, PROJECT_ROOT)
    indexed = "\n".join(d.text for d in build_documents(resources, chunks))
    for a in load_bulletin(DEFAULT_BULLETIN_PATH).announcements:
        assert a.title not in indexed and a.description not in indexed
    evidence = KeywordRetriever(resources, chunks).retrieve("winter break closing checklist demo")
    assert all("[Demo]" not in e.text for e in evidence)


# --- Streamlit integration: top-level navigation (Resources | Staff Bulletin) ----------------------


def run_app(monkeypatch, bulletin_path=None, catalog_path=None):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "")
    for var, value in (("RESLINK_BULLETIN_PATH", bulletin_path), ("RESLINK_CATALOG_PATH", catalog_path)):
        if value is not None:
            monkeypatch.setenv(var, str(value))
        else:
            monkeypatch.delenv(var, raising=False)
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def go(at, section):
    at.button_group(key="nav_section").set_value(section).run()
    assert not at.exception, at.exception
    return at


def titles(at):
    """Announcement titles in display order (titles are Markdown-escaped, so backslashes are removed)."""
    values = [m.value.replace("\\", "") for m in at.markdown]
    return [v.strip("*") for v in values if v.startswith("**[Demo]")]


def test_two_separate_top_level_sections(monkeypatch):
    at = run_app(monkeypatch)
    nav = at.button_group(key="nav_section")
    assert len(nav.options) == 2 and nav.options[0].endswith("Resources") and nav.options[1].endswith("Staff Bulletin")
    assert nav.value == "Resources"
    # Resources: every category tab, no bulletin content.
    from reslink.models import CATEGORIES

    assert [t.label for t in at.tabs] == list(CATEGORIES.values())
    assert titles(at) == [] and not any("fictional" in w.value for w in at.warning)
    # Staff Bulletin: bulletin only, no resource-category tabs.
    go(at, "Staff Bulletin")
    assert len(at.tabs) == 0
    assert len(titles(at)) == 8
    go(at, "Resources")
    assert [t.label for t in at.tabs] == list(CATEGORIES.values()) and at.get("link_button")


def test_bulletin_shows_demo_banner_pinned_first_and_no_search(monkeypatch):
    at = go(run_app(monkeypatch), "Staff Bulletin")
    assert any("fictional" in w.value for w in at.warning)
    assert len(at.text_input) == 0  # search box removed from the UI
    shown = titles(at)
    assert len(shown) == 8
    assert shown[:2] == ["[Demo] Building staff meeting moved to Thursday", "[Demo] Winter break closing checklists due"]
    assert shown[2] == "[Demo] Front desk schedule swap requests"  # newest regular item next
    assert any("Showing 8 of 8" in c.value for c in at.caption)


def test_bulletin_category_filter(monkeypatch):
    at = go(run_app(monkeypatch), "Staff Bulletin")
    at.button_group(key="bulletin_categories").set_value(["deadlines"]).run()
    assert titles(at) == ["[Demo] Winter break closing checklists due", "[Demo] Mid-semester resident check-in forms"]
    at.button_group(key="bulletin_categories").set_value(["deadlines", "meetings"]).run()
    assert titles(at)[:2] == ["[Demo] Building staff meeting moved to Thursday", "[Demo] Winter break closing checklists due"]
    assert len(titles(at)) == 4
    at.button_group(key="bulletin_categories").set_value([]).run()
    assert len(titles(at)) == 8


def test_bulletin_no_match_empty_state(monkeypatch, tmp_path):
    # Only general items exist, so filtering to Meetings matches nothing.
    path = tmp_path / "bulletins.json"
    path.write_text(json.dumps({"announcements": [item()]}), encoding="utf-8")
    at = go(run_app(monkeypatch, path), "Staff Bulletin")
    at.button_group(key="bulletin_categories").set_value(["meetings"]).run()
    assert any("No announcements in the selected categories" in i.value for i in at.info)


def test_bulletin_missing_file_empty_state(monkeypatch, tmp_path):
    at = go(run_app(monkeypatch, tmp_path / "missing.json"), "Staff Bulletin")
    assert any("No staff bulletin has been set up yet" in i.value for i in at.info)
    assert titles(at) == []


def test_bulletin_empty_list_state(monkeypatch, tmp_path):
    path = tmp_path / "bulletins.json"
    path.write_text(json.dumps({"announcements": []}), encoding="utf-8")
    at = go(run_app(monkeypatch, path), "Staff Bulletin")
    assert any("No announcements have been posted yet" in i.value for i in at.info)


def test_invalid_bulletin_does_not_break_resources_or_larry(monkeypatch, tmp_path):
    path = tmp_path / "bulletins.json"
    path.write_text(json.dumps({"announcements": [{"id": "x"}]}), encoding="utf-8")
    at = run_app(monkeypatch, path)
    assert at.tabs[0].label == "Maintenance" and at.get("link_button")  # Resources intact
    go(at, "Staff Bulletin")
    assert any("staff bulletin file couldn't be loaded" in e.value for e in at.error)
    at.button(key="larry_launch").click().run()
    at.chat_input(key="larry_input").set_value("A resident is locked out of their room").run()
    assert not at.exception
    assert any("isn't configured" in w.value for w in at.warning)  # Larry still answers (sources only)


def test_broken_catalog_only_affects_resources(monkeypatch, tmp_path):
    at = run_app(monkeypatch, catalog_path=tmp_path / "no-catalog.json")
    assert any("catalog couldn't be loaded" in e.value for e in at.error)
    go(at, "Staff Bulletin")
    assert len(titles(at)) == 8 and not at.error


def test_larry_available_in_both_sections_and_history_survives_switching(monkeypatch):
    at = run_app(monkeypatch)
    assert "larry_launch" in {b.key for b in at.button}
    at.button(key="larry_launch").click().run()
    at.chat_input(key="larry_input").set_value("Where can I see my floor roster?").run()
    go(at, "Staff Bulletin")
    assert at.session_state["larry_open"] is True and len(at.session_state["larry_history"]) == 1
    assert at.chat_input(key="larry_input")  # panel still there on the bulletin
    at.chat_input(key="larry_input").set_value("What is the quiet hours policy?").run()
    at.button_group(key="bulletin_categories").set_value(["meetings"]).run()
    go(at, "Resources")
    assert [q for q, _ in at.session_state["larry_history"]] == [
        "Where can I see my floor roster?", "What is the quiet hours policy?"]
    at.button(key="larry_close").click().run()
    go(at, "Staff Bulletin")
    assert "larry_launch" in {b.key for b in at.button}  # launcher on the bulletin too
    assert len(at.session_state["larry_history"]) == 2


def test_section_nav_cannot_be_deselected(monkeypatch):
    at = run_app(monkeypatch)
    at.button_group(key="nav_section").set_value(None).run()
    assert not at.exception
    assert at.tabs  # still showing a section (Resources)


# --- read / unread (session-only) ------------------------------------------------------------------

import hashlib  # noqa: E402

from reslink.bulletin import STATUS_ALL, STATUS_READ, STATUS_UNREAD, filter_by_status, toggle_read, unread_count  # noqa: E402


def test_status_helpers():
    read = set()
    assert unread_count(ITEMS, read) == 4
    toggle_read(read, "b")
    assert read == {"b"} and unread_count(ITEMS, read) == 3
    assert [a.id for a in filter_by_status(ITEMS, read, STATUS_READ)] == ["b"]
    assert [a.id for a in filter_by_status(ITEMS, read, STATUS_UNREAD)] == ["a", "c", "d"]  # order kept
    assert filter_by_status(ITEMS, read, STATUS_ALL) == ITEMS
    toggle_read(read, "b")
    assert read == set()


def unread_badges(at):
    return sum(1 for m in at.markdown if "badge[" in m.value and "Unread]" in m.value)


def toggle_labels(at):
    return {b.key.removeprefix("bulletin_toggle_"): b.label for b in at.button if (b.key or "").startswith("bulletin_toggle_")}


def status(at, value):
    at.button_group(key="bulletin_status").set_value(value).run()
    assert not at.exception, at.exception
    return at


def bulletin_app(monkeypatch):
    return go(run_app(monkeypatch), "Staff Bulletin")


def test_all_announcements_initially_unread_and_viewing_never_marks_read(monkeypatch):
    at = bulletin_app(monkeypatch)
    assert at.session_state["bulletin_read_ids"] == set()
    assert unread_badges(at) == 8
    assert set(toggle_labels(at).values()) == {"Mark as read"}
    assert at.button_group(key="bulletin_status").options == ["All", "Unread (8)", "Read"]
    at.run()  # just viewing again
    assert at.session_state["bulletin_read_ids"] == set()


def test_mark_read_then_unread(monkeypatch):
    at = bulletin_app(monkeypatch)
    at.button(key="bulletin_toggle_demo-003").click().run()
    assert at.session_state["bulletin_read_ids"] == {"demo-003"}
    assert toggle_labels(at)["demo-003"] == "Mark as unread"
    assert unread_badges(at) == 7
    assert at.button_group(key="bulletin_status").options[1] == "Unread (7)"
    assert any("7 unread" in c.value for c in at.caption)
    at.button(key="bulletin_toggle_demo-003").click().run()
    assert at.session_state["bulletin_read_ids"] == set()
    assert toggle_labels(at)["demo-003"] == "Mark as read" and unread_badges(at) == 8


def test_all_unread_read_filters_and_order(monkeypatch):
    at = bulletin_app(monkeypatch)
    for key in ("demo-001", "demo-005"):  # a pinned item and the newest regular item
        at.button(key=f"bulletin_toggle_{key}").click().run()
    status(at, "read")
    assert titles(at) == ["[Demo] Building staff meeting moved to Thursday", "[Demo] Front desk schedule swap requests"]
    assert unread_badges(at) == 0
    status(at, "unread")
    shown = titles(at)
    assert len(shown) == 6 and shown[0] == "[Demo] Winter break closing checklists due"  # remaining pinned first
    assert shown[1] == "[Demo] December floor program proposals"  # then newest-first (Nov 11)
    status(at, "all")
    assert len(titles(at)) == 8


def test_combined_category_and_status_filters(monkeypatch):
    at = bulletin_app(monkeypatch)
    at.button(key="bulletin_toggle_demo-002").click().run()  # pinned deadline -> read
    at.button_group(key="bulletin_categories").set_value(["deadlines"]).run()
    status(at, "unread")
    assert titles(at) == ["[Demo] Mid-semester resident check-in forms"]
    status(at, "read")
    assert titles(at) == ["[Demo] Winter break closing checklists due"]
    at.button_group(key="bulletin_categories").set_value(["general"]).run()
    assert titles(at) == []
    assert any("No announcements marked as read match" in i.value for i in at.info)


def test_status_empty_states(monkeypatch):
    at = bulletin_app(monkeypatch)
    status(at, "read")
    assert any("No announcements marked as read match" in i.value for i in at.info)
    status(at, "unread")
    for key in list(toggle_labels(at)):
        at.button(key=f"bulletin_toggle_{key}").click().run()
    assert titles(at) == []
    assert any("You're all caught up" in i.value for i in at.info)
    assert at.button_group(key="bulletin_status").options[1] == "Unread (0)"


def test_read_status_survives_navigation_filters_and_larry(monkeypatch):
    at = bulletin_app(monkeypatch)
    at.button(key="larry_launch").click().run()
    at.chat_input(key="larry_input").set_value("Where can I see my floor roster?").run()
    at.button(key="bulletin_toggle_demo-004").click().run()
    at.button_group(key="bulletin_categories").set_value(["meetings"]).run()
    go(at, "Resources")
    at.button(key="larry_close").click().run()
    at.button(key="larry_launch").click().run()
    go(at, "Staff Bulletin")
    assert at.session_state["bulletin_read_ids"] == {"demo-004"}
    assert toggle_labels(at)["demo-004"] == "Mark as unread"
    assert [q for q, _ in at.session_state["larry_history"]] == ["Where can I see my floor roster?"]
    assert at.session_state["larry_open"] is True


def test_read_status_never_changes_json_source(monkeypatch):
    before = hashlib.sha256(DEFAULT_BULLETIN_PATH.read_bytes()).hexdigest()
    at = bulletin_app(monkeypatch)
    for key in ("demo-001", "demo-002", "demo-001"):
        at.button(key=f"bulletin_toggle_{key}").click().run()
    status(at, "read")
    assert hashlib.sha256(DEFAULT_BULLETIN_PATH.read_bytes()).hexdigest() == before
