"""Streamlit rendering helpers. Display only: no loading, retrieval, or model calls."""

from __future__ import annotations

import re
from datetime import date

import streamlit as st

from reslink.bulletin import (
    BULLETIN_CATEGORIES,
    STATUS_ALL,
    STATUS_READ,
    STATUS_UNREAD,
    STATUSES,
    Announcement,
    Bulletin,
    BulletinError,
    filter_by_status,
    is_read,
    select,
    toggle_read,
    unread_count,
)
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
    sections = [c for c in citations if c.section]
    pages = sorted({c.page for c in citations if c.page is not None and not c.section})
    # Link comes from the validated catalog entry (plus a page anchor for cited PDF pages).
    link = Citation(resource, pages[0] if pages else None).link
    with st.container(border=True):
        if link:
            st.link_button(resource.title, link)
        else:  # e.g. a manual transcription: never invent a link
            st.markdown(f"**{resource.title}**")
        if resource.description:
            st.write(resource.description)
        for citation in sections:
            st.caption(f"Cited: {citation.label}")
        login = " · sign-in required" if resource.requires_login else ""
        cited = f" · cited page(s): {', '.join(map(str, pages))}" if pages else ""
        where = resource.url if resource.url else "no public link · not independently verified as current"
        st.caption(f"{resource.category_label} · {resource.content_type}{login}{cited} · {where}")


def render_dashboard(grouped: dict[str, list[Resource]]) -> None:
    """Resource category tabs in catalog order."""
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


# --- Top-level navigation -------------------------------------------------------------------------

SECTION_RESOURCES = "Resources"
SECTION_BULLETIN = "Staff Bulletin"
SECTIONS = (SECTION_RESOURCES, SECTION_BULLETIN)
SECTION_ICONS = {SECTION_RESOURCES: ":material/folder_open:", SECTION_BULLETIN: ":material/campaign:"}


def render_section_nav() -> str:
    """Compact top-level switch between Resources and the Staff Bulletin.

    ``required=True`` means a section is always selected (it can't be clicked into "none").
    Switching sections is a normal rerun; Larry's state lives in session_state and is untouched.
    """
    choice = st.segmented_control(
        "Section", options=list(SECTIONS), default=SECTION_RESOURCES, required=True,
        format_func=lambda s: f"{SECTION_ICONS[s]} {s}", key="nav_section",
        label_visibility="collapsed",
    )
    return choice or SECTION_RESOURCES


# --- Staff Bulletin (read-only; independent of Larry and the AI pipeline) -------------------------

BULLETIN_TAB_LABEL = SECTION_BULLETIN
BULLETIN_MISSING = (
    "No staff bulletin has been set up yet. Announcements will appear here once "
    "data/bulletins.json is added."
)
BULLETIN_EMPTY = "No announcements have been posted yet."
BULLETIN_NO_MATCH = (
    "No announcements in the selected categories. Clear or change the category filters to see more."
)
BULLETIN_NO_UNREAD = "You're all caught up: no unread announcements match the selected filters."
BULLETIN_NO_READ = (
    "No announcements marked as read match the selected filters. Use \"Mark as read\" on an "
    "announcement to move it here."
)
READ_IDS_KEY = "bulletin_read_ids"  # session-only set of announcement IDs the user marked as read
STATUS_LABELS = {STATUS_ALL: "All", STATUS_UNREAD: "Unread", STATUS_READ: "Read"}


def _read_ids() -> set[str]:
    return st.session_state.setdefault(READ_IDS_KEY, set())


def _toggle(announcement_id: str) -> None:
    toggle_read(_read_ids(), announcement_id)


def _md_escape(text: str) -> str:
    """Show file text literally (no accidental links/emphasis from [], *, _, `)."""
    return re.sub(r"([\\\[\]*_`])", r"\\\1", text)


def _format_date(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def _render_announcement(item: Announcement, read: bool) -> None:
    with st.container(border=True):
        with st.container(horizontal=True):
            if not read:
                st.badge("Unread", icon=":material/fiber_manual_record:", color="gray")
            if item.pinned:
                st.badge("Pinned", icon=":material/push_pin:", color="orange")
            st.badge(item.category_label, color="blue")
            if item.due:
                st.badge(f"Due {_format_date(item.due)}", icon=":material/event:", color="red")
        st.markdown(f"**{_md_escape(item.title)}**")
        st.markdown(_md_escape(item.description))
        # Button on the left: the right edge is where Larry's floating launcher sits.
        with st.container(horizontal=True, vertical_alignment="center"):
            # Explicit action only: displaying an announcement never marks it as read.
            st.button("Mark as unread" if read else "Mark as read", key=f"bulletin_toggle_{item.id}",
                      icon=":material/mark_email_unread:" if read else ":material/done:",
                      type="tertiary", on_click=_toggle, args=(item.id,))
            st.caption(f"· Posted {_format_date(item.published)}")


@st.fragment
def render_bulletin(bulletin: Bulletin | None, error: BulletinError | None = None) -> None:
    """Category filter + pinned-first, newest-first list. A fragment: filtering doesn't rerun the app."""
    st.subheader(BULLETIN_TAB_LABEL)
    if error is not None:
        st.error("The staff bulletin file couldn't be loaded, so no announcements are shown.")
        with st.expander("Details"):
            for message in error.errors:
                st.write(f"- {message}")
        return
    if bulletin is None or bulletin.source_missing:
        st.info(BULLETIN_MISSING)
        return
    if bulletin.demo_data:
        st.warning(bulletin.notice or "Demonstration data: these announcements are fictional.",
                   icon=":material/info:")
    if not bulletin.announcements:
        st.info(BULLETIN_EMPTY)
        return
    read_ids = _read_ids()
    unread = unread_count(bulletin.announcements, read_ids)
    status = st.segmented_control(
        "Status", options=list(STATUSES), default=STATUS_ALL, required=True, key="bulletin_status",
        format_func=lambda s: f"Unread ({unread})" if s == STATUS_UNREAD else STATUS_LABELS[s],
    ) or STATUS_ALL
    categories = st.pills("Category", options=list(BULLETIN_CATEGORIES), selection_mode="multi",
                          format_func=BULLETIN_CATEGORIES.get, key="bulletin_categories")
    # Category filter + pinned-first/newest-first order, then the read-status filter (order kept).
    shown = filter_by_status(select(bulletin, "", categories or ()), read_ids, status)
    st.caption(f"Showing {len(shown)} of {len(bulletin.announcements)} announcements · {unread} unread")
    if not shown:
        st.info({STATUS_UNREAD: BULLETIN_NO_UNREAD, STATUS_READ: BULLETIN_NO_READ}.get(status, BULLETIN_NO_MATCH))
    for item in shown:
        _render_announcement(item, is_read(item, read_ids))


def render_response(response: AssistantResponse) -> None:
    """Show an assistant response. Links come only from response.resources (catalog entries)."""
    if response.notice:
        if response.status is Status.ERROR:
            st.warning(response.notice)
        else:
            st.info(response.notice)
    if response.answer:
        st.markdown(response.answer)
    for caveat in response.caveats:  # source-quality notices added by code, not the model
        st.warning(caveat)
    if response.resources:
        label = "Sources" if response.status is Status.GROUNDED else "Related verified resources"
        st.caption(label)
        for resource in response.resources:
            _render_resource_card(
                resource, tuple(c for c in response.citations if c.resource.id == resource.id)
            )
