"""Streamlit entry point for ResLink AI. Run with: streamlit run app.py"""

from pathlib import Path

import streamlit as st

from reslink import ui
from reslink.assistant import GeminiGenerator, answer_question
from reslink.catalog import CatalogError, group_by_category, load_catalog
from reslink.config import load_env_file, load_settings
from reslink.ingest import load_index
from reslink.larry import render_larry
from reslink.retrieval import HybridRetriever, KeywordRetriever
from reslink.semantic import (
    CATALOG_MAX_DISTANCE,
    DEFAULT_MAX_DISTANCE,
    SemanticIndex,
    build_documents,
    fingerprint,
)

st.set_page_config(page_title="ResLink AI", page_icon="📚", layout="wide")

load_env_file()
settings = load_settings()


@st.cache_resource(show_spinner=False)
def get_generator(api_key: str, model: str) -> GeminiGenerator:
    return GeminiGenerator(api_key=api_key, model=model)


@st.cache_resource(show_spinner="Loading semantic search...")
def get_retriever(_resources, _chunks, chroma_path: str, content_key: str, index_mtime: float):
    """Built once per server process and reused across reruns (the embedding model loads once).

    The cache key is the content fingerprint + index file time, so editing the catalog,
    rebuilding chunks, or rebuilding the Chroma index yields a fresh retriever.
    Any semantic problem falls back to keyword-only retrieval with a reason.
    """
    keyword = KeywordRetriever(_resources, _chunks)
    try:
        index, status = SemanticIndex.open(Path(chroma_path), _resources, _chunks)
    except Exception as exc:  # never let semantic setup break the app
        index, status = None, f"semantic index failed to load ({type(exc).__name__})"
    retriever = HybridRetriever(
        keyword, index, max_distance=DEFAULT_MAX_DISTANCE, catalog_max_distance=CATALOG_MAX_DISTANCE
    )
    return retriever, status


def _index_mtime(path: Path) -> float:
    db = path / "chroma.sqlite3"
    return db.stat().st_mtime if db.is_file() else 0.0


ui.render_header()

try:
    resources = load_catalog(settings.catalog_path)
except CatalogError as error:
    resources, chunks, index_warnings = [], [], []
    catalog_error = error
else:
    chunks, index_warnings = load_index(settings.index_path, resources)
    catalog_error = None

retriever, retrieval_status = get_retriever(
    resources,
    chunks,
    str(settings.chroma_path),
    fingerprint(build_documents(resources, chunks)),
    _index_mtime(settings.chroma_path),
)

if catalog_error is not None:
    ui.render_sidebar_status(settings, None, retrieval_status=retrieval_status)
    ui.render_catalog_error(catalog_error)
else:
    ui.render_sidebar_status(settings, len(resources), len(chunks), index_warnings, retrieval_status)
    ui.render_dashboard(group_by_category(resources))

generator = (
    get_generator(settings.gemini_api_key, settings.gemini_model) if settings.gemini_configured else None
)


def ask(question: str):
    """The only bridge from the UI to retrieval + Gemini (assistant logic unchanged)."""
    return answer_question(question, retriever, generator)


render_larry(ask)
