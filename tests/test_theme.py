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
    # A shared light/dark token, falling back to the theme-aware system color.
    assert re.search(r"background:\s*var\(--rl-surface,\s*Canvas\)\s*;", panel)
    assert "color:" not in re.sub(r"(background|border|box-shadow)[^;]*;", "", panel), (
        "panel must inherit Streamlit's text color, not set its own"
    )


# --- Blackout theme (config.toml + reslink/static/theme.css) ---------------------------

THEME_CSS = PROJECT_ROOT / "reslink" / "static" / "theme.css"


def _theme_css() -> str:
    return re.sub(r"/\*.*?\*/", "", THEME_CSS.read_text(encoding="utf-8"), flags=re.S)


def test_config_defines_both_themes_with_blackout_dark():
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    dark, light = theme["dark"], theme["light"]
    assert dark["backgroundColor"] == "#0A0A0A" and dark["sidebar"]["backgroundColor"] == "#1C1C1C"
    assert dark["primaryColor"] == "#FF8200" and dark["textColor"] == "#FFFFFF"
    assert {"backgroundColor", "primaryColor", "textColor"} <= set(light)
    # Only shared, non-color options at the top level (colors there would apply to both modes).
    top = {k for k, v in theme.items() if not isinstance(v, dict)}
    assert top <= {"font", "headingFont", "headingFontWeights", "baseRadius", "showWidgetBorder"}
    assert theme["font"].startswith("Inter:") and theme["headingFont"].startswith("Manrope:")


def test_theme_tokens_switch_with_light_dark():
    """Every color token except the fixed Tennessee Orange set follows the active theme."""
    root = re.search(r":root\s*\{([^}]*)\}", _theme_css()).group(1)
    tokens = dict(re.findall(r"(--rl-[\w-]+):\s*([^;]+);", root))
    fixed = {"--rl-orange", "--rl-orange-hover", "--rl-orange-active", "--rl-on-orange",
             "--rl-tooltip-bg", "--rl-tooltip-text"}  # brand colors, same in both themes
    assert fixed <= set(tokens)
    for name, value in tokens.items():
        if name not in fixed:
            assert value.startswith("light-dark("), name


def test_colors_only_in_tokens():
    """Outside :root, theme.css uses tokens only (one place to change a color)."""
    css = re.sub(r":root\s*\{[^}]*\}", "", _theme_css())
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css), "hex color outside :root tokens"
    assert not re.search(r"\b(rgba?|hsla?|light-dark)\(", css), "color function outside :root tokens"


def test_injected_css_has_no_markup():
    """Streamlit's HTML sanitizer drops a whole <style> block whose text looks like a tag
    (this silently removed all of larry.css once, via a comment mentioning an img tag)."""
    for path in (LARRY_CSS, THEME_CSS):
        assert not re.search(r"<[/!\w]", path.read_text(encoding="utf-8")), path.name


def test_launcher_shows_larry_photo():
    css = _css_without_comments()
    rule = re.search(r"\.st-key-larry-launcher button\s*\{([^}]*)\}", css).group(1)
    for decl in ('background-image: url("app/static/larry.png")', "background-size: cover",
                 "background-position: center", "overflow: hidden", "border: 3px solid var(--rl-orange"):
        assert decl in rule, decl
    assert (PROJECT_ROOT / "static" / "larry.png").is_file()
    assert tomllib.loads(CONFIG.read_text(encoding="utf-8"))["server"]["enableStaticServing"] is True


def test_launcher_tooltip_on_hover_and_focus():
    css = _css_without_comments()
    tip = re.search(r"\.st-key-larry-launcher::before\s*\{([^}]*)\}", css).group(1)
    assert 'content: "Chat with Larry" / "";' in tip  # empty alt text: no duplicate for screen readers
    for decl in ("pointer-events: none", "opacity: 0", "visibility: hidden", "border-radius: 8px",
                 "font-family: Inter", "border: 1px solid var(--rl-orange", "bottom: calc(100% + 10px)"):
        assert decl in tip, decl
    assert re.search(r"transition: opacity 1[5-9]\dms", tip)
    assert ".st-key-larry-launcher:has(button:hover)::before" in css
    assert ".st-key-larry-launcher:has(button:focus-visible)::before" in css
    # Streamlit's own help tooltip would duplicate it.
    source = (PROJECT_ROOT / "reslink" / "larry.py").read_text(encoding="utf-8")
    launcher_call = re.search(r"st\.button\(LAUNCHER_LABEL[^)]*\)", source).group(0)
    assert "help=" not in launcher_call


def test_launcher_is_a_circle_at_both_sizes():
    css = _css_without_comments()
    rules = re.findall(r"\.st-key-larry-launcher button\s*\{([^}]*)\}", css)
    assert any("width: 72px" in r and "height: 72px" in r and "border-radius: 50%" in r for r in rules)
    mobile = css[css.index("@media (max-width: 640px)"):]
    assert re.search(r"\.st-key-larry-launcher button\s*\{[^}]*width: 64px;[^}]*height: 64px;", mobile)
    for state in (":hover", ":active", ":focus-visible"):
        assert f".st-key-larry-launcher button{state}" in css, state
