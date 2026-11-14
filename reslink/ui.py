"""Streamlit rendering helpers. Display only: no loading, retrieval, or model calls."""

from __future__ import annotations

import streamlit as st

from reslink.catalog import CatalogError
from reslink.config import Settings
from reslink.models import CATEGORIES, AssistantResponse, Citation, Resource, Status


def render_header() -> None:
    st.title("ResLink AI")
    st.subheader("Your Intelligent RA Resource Navigator")
    st.caption(
        "Finds verified public University of Tennessee resources and links to the "
        "original source. It doesn't submit forms or replace official guidance."
    )


def render_sidebar_status(
    settings: Settings,
    resource_count: int | None,
    chunk_count: int = 0,
    index_warnings: list[str] | None = None,
    retrieval_status: str | None = None,
) -> None:
    with st.sidebar:
        st.header("Status")
        if resource_count is None:
            st.write("Catalog: unavailable")
        else:
            st.write(f"Verified resources: {resource_count}")
        if chunk_count:
            st.write(f"Indexed document passages: {chunk_count}")
        else:
            st.write("Document index: not built (run `python -m scripts.build_index`)")
        if retrieval_status is not None:
            if retrieval_status == "ready":
                st.write("Retrieval: hybrid (keyword + semantic)")
            else:
                st.write("Retrieval: keyword only")
                st.caption(f"Semantic search unavailable: {retrieval_status}")
        for warning in index_warnings or []:
            st.warning(warning)
        # Never display the key itself, only whether one is configured.
        st.write("Gemini: configured" if settings.gemini_configured else "Gemini: not configured")


def render_catalog_error(error: CatalogError) -> None:
    st.error("The resource catalog couldn't be loaded, so no resources are shown.")
    with st.expander("Details"):
        for message in error.errors:
            st.write(f"- {message}")


def _render_resource_card(resource: Resource, citations: tuple[Citation, ...] = ()) -> None:
    pages = sorted({c.page for c in citations if c.page is not None})
    # Link comes from the validated catalog entry (plus a page anchor for cited PDF pages).
    link = Citation(resource, pages[0] if pages else None).link
    with st.container(border=True):
        st.link_button(resource.title, link)
        if resource.description:
            st.write(resource.description)
        login = " · sign-in required" if resource.requires_login else ""
        cited = f" · cited page(s): {', '.join(map(str, pages))}" if pages else ""
        st.caption(f"{resource.category_label} · {resource.content_type}{login}{cited} · {resource.url}")


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


def render_response(response: AssistantResponse) -> None:
    """Show an assistant response. Links come only from response.resources (catalog entries)."""
    if response.notice:
        if response.status is Status.ERROR:
            st.warning(response.notice)
        else:
            st.info(response.notice)
    if response.answer:
        st.markdown(response.answer)
    if response.resources:
        label = "Sources" if response.status is Status.GROUNDED else "Related verified resources"
        st.caption(label)
        for resource in response.resources:
            _render_resource_card(
                resource, tuple(c for c in response.citations if c.resource.id == resource.id)
            )
