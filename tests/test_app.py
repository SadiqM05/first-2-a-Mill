"""Smoke tests that run app.py headlessly with Streamlit's AppTest."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import PROJECT_ROOT

APP = str(PROJECT_ROOT / "app.py")


def run_app(monkeypatch, catalog_path: Path | None = None) -> AppTest:
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
    assert len(at.tabs) == 4
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


def test_chat_never_fakes_an_answer(monkeypatch, tmp_path):
    path = tmp_path / "resources.json"
    path.write_text("[]", encoding="utf-8")
    at = run_app(monkeypatch, path)
    at.chat_input[0].set_value("Where do I submit my weekly RA report?").run()
    assert not at.exception
    assert any("isn't connected yet" in i.value for i in at.info)


@pytest.mark.parametrize("module", ["models", "config", "catalog"])
def test_core_modules_do_not_import_streamlit(module):
    tree = ast.parse((PROJECT_ROOT / "reslink" / f"{module}.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "streamlit" not in imported
