"""Streamlit entry point for ResLink AI. Run with: streamlit run app.py"""

import streamlit as st

from reslink import ui
from reslink.assistant import GeminiGenerator, answer_question
from reslink.catalog import CatalogError, group_by_category, load_catalog
from reslink.config import load_env_file, load_settings
from reslink.ingest import load_index
from reslink.retrieval import KeywordRetriever

st.set_page_config(page_title="ResLink AI", page_icon="📚", layout="wide")

load_env_file()
settings = load_settings()


@st.cache_resource(show_spinner=False)
def get_generator(api_key: str, model: str) -> GeminiGenerator:
    return GeminiGenerator(api_key=api_key, model=model)


ui.render_header()

try:
    resources = load_catalog(settings.catalog_path)
except CatalogError as error:
    resources, chunks = [], []
    ui.render_sidebar_status(settings, resource_count=None)
    ui.render_catalog_error(error)
else:
    chunks, index_warnings = load_index(settings.index_path, resources)
    ui.render_sidebar_status(settings, len(resources), len(chunks), index_warnings)
    ui.render_dashboard(group_by_category(resources))

generator = (
    get_generator(settings.gemini_api_key, settings.gemini_model) if settings.gemini_configured else None
)
retriever = KeywordRetriever(resources, chunks)

history = st.session_state.setdefault("history", [])
question = st.chat_input("What do you need help with?")
if question:
    with st.spinner("Looking up verified resources..."):
        history.append((question, answer_question(question, retriever, generator)))

ui.render_chat_history(history)
