"""Smoke tests that run app.py headlessly with Streamlit's AppTest."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT
from reslink.models import CATEGORIES

APP = str(PROJECT_ROOT / "app.py")


def run_app(monkeypatch, catalog_path: Path | None = None) -> AppTest:
    # Blank (not unset) so a developer's .env can't enable real Gemini calls during tests.
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


def test_empty_catalog_shows_honest_empty_state(monkeypatch, tmp_path):
    path = tmp_path / "resources.json"
    path.write_text("[]", encoding="utf-8")
    at = run_app(monkeypatch, path)
    assert at.title[0].value == "ResLink AI"
    assert any("No verified resources have been added yet" in i.value for i in at.info)
    # Resources section (default): category tabs in catalog order only; the Staff Bulletin is a
    # separate top-level section (Milestone 5 navigation refinement).
    assert at.button_group(key="nav_section").value == "Resources"
    assert [t.label for t in at.tabs] == list(CATEGORIES.values())
    assert not at.error


def test_real_catalog_renders_without_errors(monkeypatch):
    at = run_app(monkeypatch)
    assert not at.error


def test_placeholder_catalog_is_refused_by_app(monkeypatch, placeholder_catalog_path):
    at = run_app(monkeypatch, placeholder_catalog_path)
    assert at.error and "couldn't be loaded" in at.error[0].value
    # No resource buttons/links rendered from placeholder data.
    assert not at.get("link_button")


def test_resource_cards_render_links_from_catalog(monkeypatch, placeholder_catalog_path):
    # Test-only: lift the placeholder guard so fixture cards can be rendered.
    import reslink.catalog

    monkeypatch.setattr(reslink.catalog, "PLACEHOLDER_HOSTS", frozenset())
    at = run_app(monkeypatch, placeholder_catalog_path)
    assert not at.error
    buttons = at.get("link_button")
    assert len(buttons) == 3
    urls = {b.proto.url for b in buttons}
    assert urls == {
        "https://example.org/placeholder/maintenance",
        "https://example.org/placeholder/reporting.pdf",
        "https://www.example.com/placeholder/reporting-2",
    }


def test_missing_catalog_shows_error(monkeypatch, tmp_path):
    at = run_app(monkeypatch, tmp_path / "missing.json")
    assert at.error


@pytest.mark.parametrize("module", ["models", "config", "catalog", "retrieval", "assistant", "ingest"])
def test_core_modules_do_not_import_streamlit(module):
    tree = ast.parse((PROJECT_ROOT / "reslink" / f"{module}.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "streamlit" not in imported


def test_erezlife_link_on_ra_portals_tab(monkeypatch):
    at = run_app(monkeypatch)
    ra_portals = next(t for t in at.tabs if t.label == "RA Portals")
    buttons = {b.proto.label: b.proto.url for b in ra_portals.get("link_button")}
    assert buttons["eRezLife \u2014 RA Reporting & Programming"] == "https://utk.erezlife.com/"
