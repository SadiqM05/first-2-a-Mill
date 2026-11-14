"""Regression guards for the Light/Dark/System theme toggle.

Streamlit removes the theme choice from its main menu when `.streamlit/config.toml`
sets `[theme] base`, and Larry's panel must follow the active theme instead of using
literal colors (which is what led to the theme being pinned in the first place).
"""

import re
import tomllib

from conftest import PROJECT_ROOT

CONFIG = PROJECT_ROOT / ".streamlit" / "config.toml"
LARRY_CSS = PROJECT_ROOT / "reslink" / "static" / "larry.css"


def _css_without_comments() -> str:
    return re.sub(r"/\*.*?\*/", "", LARRY_CSS.read_text(encoding="utf-8"), flags=re.S)


def test_config_does_not_pin_theme():
    if not CONFIG.exists():
        return
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8")).get("theme", {})
    assert "base" not in theme, "theme.base hides Streamlit's Light/Dark/System toggle"


def test_larry_css_has_no_literal_colors():
    css = _css_without_comments()
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css), "hex color found in larry.css"
    assert not re.search(r"\b(rgba?|hsla?)\(", css), "rgb()/hsl() color found in larry.css"


def test_larry_panel_uses_theme_aware_surface():
    css = _css_without_comments()
    panel = re.search(r"\.st-key-larry-panel\s*\{([^}]*)\}", css).group(1)
    assert re.search(r"background:\s*Canvas\s*;", panel)
    assert "color:" not in re.sub(r"(background|border|box-shadow)[^;]*;", "", panel), (
        "panel must inherit Streamlit's text color, not set its own"
    )
