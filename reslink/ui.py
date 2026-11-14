"""Streamlit rendering helpers. Display only: no loading, retrieval, or model calls."""

from __future__ import annotations

import streamlit as st

from reslink.catalog import CatalogError
from reslink.config import Settings
from reslink.models import CATEGORIES, Resource

ASSISTANT_NOT_CONNECTED = (
    "The AI assistant isn't connected yet, so I can't answer questions. "
    "Please browse the verified resources above. I won't guess at policies, "
    "deadlines, or links."
)


def render_header() -> None:
    st.title("ResLink AI")
    st.subheader("Your Intelligent RA Resource Navigator")
    st.caption(
        "Finds verified public University of Tennessee resources and links to the "
        "original source. It doesn't submit forms or replace official guidance."
    )


def render_sidebar_status(settings: Settings, resource_count: int | None) -> None:
    with st.sidebar:
        st.header("Status")
        if resource_count is None:
            st.write("Catalog: unavailable")
        else:
            st.write(f"Verified resources: {resource_count}")
        # Never display the key itself, only whether one is configured.
        st.write("Gemini: configured" if settings.gemini_configured else "Gemini: not configured")


def render_catalog_error(error: CatalogError) -> None:
    st.error("The resource catalog couldn't be loaded, so no resources are shown.")
    with st.expander("Details"):
        for message in error.errors:
            st.write(f"- {message}")


def _render_resource_card(resource: Resource) -> None:
    with st.container(border=True):
        # Link comes straight from the validated catalog entry.
        st.link_button(resource.title, resource.url)
        if resource.description:
            st.write(resource.description)
        st.caption(f"{resource.content_type} · {resource.url}")


def render_dashboard(grouped: dict[str, list[Resource]]) -> None:
    st.header("Browse resources")
    if not any(grouped.values()):
        st.info(
            "No verified resources have been added yet. "
            "Resources appear here once the team adds them to data/resources.json."
        )
    tabs = st.tabs([CATEGORIES[key] for key in grouped])
    for tab, (key, resources) in zip(tabs, grouped.items()):
        with tab:
            if not resources:
                st.write(f"No verified {CATEGORIES[key].lower()} resources yet.")
            for resource in resources:
                _render_resource_card(resource)


def render_chat(question: str | None) -> None:
    if not question:
        return
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.info(ASSISTANT_NOT_CONNECTED)
