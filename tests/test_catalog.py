import json
from pathlib import Path

import pytest

from reslink.catalog import CatalogError, group_by_category, load_catalog, parse_catalog
from reslink.config import DEFAULT_CATALOG_PATH
from reslink.models import CATEGORIES

VALID = {
    "id": "t-1",
    "title": "PLACEHOLDER test resource",
    "category": "maintenance",
    "url": "https://example.org/placeholder",
}


def entry(**overrides):
    data = dict(VALID)
    data.update(overrides)
    return {k: v for k, v in data.items() if v is not None}


def errors_for(data, allow_placeholders=True) -> list[str]:
    with pytest.raises(CatalogError) as info:
        parse_catalog(data, allow_placeholders=allow_placeholders)
    return info.value.errors


# --- the real catalog -------------------------------------------------------


def test_real_catalog_is_valid_and_has_no_placeholders():
    # Loads with placeholders disallowed, exactly as the app does.
    resources = load_catalog(DEFAULT_CATALOG_PATH)
    assert isinstance(resources, list)


# --- loading files ----------------------------------------------------------


def test_placeholder_fixture_loads_when_explicitly_allowed(placeholder_catalog_path):
    resources = load_catalog(placeholder_catalog_path, allow_placeholders=True)
    assert [r.id for r in resources] == [
        "placeholder-maintenance-001",
        "placeholder-reporting-001",
        "placeholder-reporting-002",
    ]
    first = resources[0]
    assert first.keywords == ("repair", "broken")
    assert first.category_label == "Maintenance"
    assert resources[1].content_type == "pdf"
    assert resources[2].content_type == "webpage"  # default


def test_placeholder_hosts_rejected_by_default(placeholder_catalog_path):
    with pytest.raises(CatalogError) as info:
        load_catalog(placeholder_catalog_path)
    assert len(info.value.errors) == 3
    assert all("placeholder host" in e for e in info.value.errors)


def test_empty_catalog_is_valid(tmp_path: Path):
    path = tmp_path / "resources.json"
    path.write_text("[]", encoding="utf-8")
    assert load_catalog(path) == []


def test_missing_file(tmp_path: Path):
    with pytest.raises(CatalogError, match="not found"):
        load_catalog(tmp_path / "nope.json")


def test_invalid_json(tmp_path: Path):
    path = tmp_path / "resources.json"
    path.write_text("[{bad json", encoding="utf-8")
    with pytest.raises(CatalogError, match="not valid JSON"):
        load_catalog(path)


# --- schema validation ------------------------------------------------------


def test_top_level_must_be_list():
    assert "JSON array" in errors_for({"resources": []})[0]


def test_entry_must_be_object():
    assert "JSON object" in errors_for(["not an object"])[0]


@pytest.mark.parametrize("field", ["id", "title", "category", "url"])
def test_required_fields(field):
    errors = errors_for([entry(**{field: None})])
    assert any(f"'{field}' is required" in e for e in errors)


@pytest.mark.parametrize("field", ["id", "title", "category", "url"])
def test_required_fields_reject_blank(field):
    errors = errors_for([entry(**{field: "   "})])
    assert any(f"'{field}' is required" in e for e in errors)


def test_unknown_category():
    assert any("category 'housing'" in e for e in errors_for([entry(category="housing")]))


@pytest.mark.parametrize(
    "url", ["http://example.org/x", "example.org/x", "/relative/path", "ftp://example.org/x"]
)
def test_url_must_be_absolute_https(url):
    assert any("https://" in e for e in errors_for([entry(url=url)]))


def test_unknown_content_type():
    assert any("content_type" in e for e in errors_for([entry(content_type="video")]))


def test_unknown_fields_rejected():
    errors = errors_for([entry(verified_by="someone")])
    assert any("unknown field" in e for e in errors)


@pytest.mark.parametrize("keywords", ["repair", [1, 2], ["ok", ""]])
def test_keywords_must_be_list_of_strings(keywords):
    assert any("keywords" in e for e in errors_for([entry(keywords=keywords)]))


def test_description_must_be_string():
    assert any("description" in e for e in errors_for([entry(description=["x"])]))


def test_duplicate_ids():
    errors = errors_for([entry(), entry(title="Other")])
    assert any("duplicate id 't-1'" in e for e in errors)


def test_all_errors_reported_together():
    errors = errors_for([entry(category="nope"), entry(id="t-2", url="http://x")])
    assert len(errors) == 2


def test_whitespace_is_trimmed():
    [r] = parse_catalog([entry(title="  Spaced  ", keywords=[" a "])], allow_placeholders=True)
    assert r.title == "Spaced"
    assert r.keywords == ("a",)


# --- grouping ---------------------------------------------------------------


def test_group_by_category_keeps_every_category_in_order(placeholder_catalog_path):
    resources = load_catalog(placeholder_catalog_path, allow_placeholders=True)
    grouped = group_by_category(resources)
    assert list(grouped) == list(CATEGORIES)
    assert len(grouped["maintenance"]) == 1
    assert len(grouped["reporting"]) == 2
    assert grouped["programming"] == []
    assert grouped["policies"] == []


def test_group_by_category_sorts_titles():
    resources = parse_catalog(
        [entry(id="a", title="Zeta"), entry(id="b", title="alpha")], allow_placeholders=True
    )
    titles = [r.title for r in group_by_category(resources)["maintenance"]]
    assert titles == ["alpha", "Zeta"]


def test_real_catalog_file_is_utf8_json_array():
    data = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
