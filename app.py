"""Streamlit entry point for ResLink AI. Run with: streamlit run app.py"""

import streamlit as st

from reslink import ui
from reslink.catalog import CatalogError, group_by_category, load_catalog
from reslink.config import load_env_file, load_settings

st.set_page_config(page_title="ResLink AI", page_icon="📚", layout="wide")

load_env_file()
settings = load_settings()

ui.render_header()

try:
    resources = load_catalog(settings.catalog_path)
except CatalogError as error:
    ui.render_sidebar_status(settings, resource_count=None)
    ui.render_catalog_error(error)
else:
    ui.render_sidebar_status(settings, resource_count=len(resources))
    ui.render_dashboard(group_by_category(resources))

ui.render_chat(st.chat_input("What do you need help with?"))
