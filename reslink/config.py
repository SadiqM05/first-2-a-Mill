"""Runtime settings read from environment variables.

Secrets come from the environment (optionally populated from a local ``.env``).
No model name is hardcoded: if ``GEMINI_MODEL`` is unset, the assistant is
reported as not configured.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "resources.json"
DEFAULT_INDEX_PATH = PROJECT_ROOT / "data" / "index" / "chunks.json"
DEFAULT_CHROMA_PATH = PROJECT_ROOT / "data" / "index" / "chroma"
DEFAULT_BULLETIN_PATH = PROJECT_ROOT / "data" / "bulletins.json"
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


@dataclass(frozen=True)
class Settings:
    catalog_path: Path
    index_path: Path = DEFAULT_INDEX_PATH
    chroma_path: Path = DEFAULT_CHROMA_PATH
    bulletin_path: Path = DEFAULT_BULLETIN_PATH
    gemini_model: str | None = None
    # repr=False so the key never shows up in logs, tracebacks, or the UI.
    gemini_api_key: str | None = field(default=None, repr=False)

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_model)


def load_env_file() -> None:
    """Load ``.env`` from the project root without overriding real env vars."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Build settings from ``environ`` (defaults to ``os.environ``)."""
    env = os.environ if environ is None else environ
    catalog = _clean(env.get("RESLINK_CATALOG_PATH"))
    index = _clean(env.get("RESLINK_INDEX_PATH"))
    chroma = _clean(env.get("RESLINK_CHROMA_PATH"))
    bulletin = _clean(env.get("RESLINK_BULLETIN_PATH"))
    return Settings(
        catalog_path=Path(catalog) if catalog else DEFAULT_CATALOG_PATH,
        index_path=Path(index) if index else DEFAULT_INDEX_PATH,
        chroma_path=Path(chroma) if chroma else DEFAULT_CHROMA_PATH,
        bulletin_path=Path(bulletin) if bulletin else DEFAULT_BULLETIN_PATH,
        gemini_model=_clean(env.get("GEMINI_MODEL")),
        gemini_api_key=_clean(env.get("GEMINI_API_KEY")),
    )
