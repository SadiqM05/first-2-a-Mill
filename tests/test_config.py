from pathlib import Path

from reslink.config import DEFAULT_CATALOG_PATH, load_settings


def test_defaults_when_env_empty():
    settings = load_settings({})
    assert settings.catalog_path == DEFAULT_CATALOG_PATH
    assert settings.gemini_model is None
    assert settings.gemini_api_key is None
    assert settings.gemini_configured is False


def test_reads_env_values():
    settings = load_settings(
        {"GEMINI_API_KEY": "fake-key", "GEMINI_MODEL": " some-model ", "RESLINK_CATALOG_PATH": "x.json"}
    )
    assert settings.gemini_model == "some-model"
    assert settings.gemini_configured is True
    assert settings.catalog_path == Path("x.json")


def test_needs_both_key_and_model():
    assert load_settings({"GEMINI_API_KEY": "fake-key"}).gemini_configured is False
    assert load_settings({"GEMINI_MODEL": "m"}).gemini_configured is False
    assert load_settings({"GEMINI_API_KEY": "  ", "GEMINI_MODEL": "m"}).gemini_configured is False


def test_api_key_not_in_repr():
    assert "fake-key" not in repr(load_settings({"GEMINI_API_KEY": "fake-key"}))
