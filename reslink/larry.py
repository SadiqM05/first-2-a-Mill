"""Larry: floating chat widget for ResLink AI (Streamlit UI only).

Larry never calls retrieval or Gemini directly. ``app.py`` passes in an ``ask``
function, so this module only handles layout, session state, and rendering.

State (st.session_state):
- ``larry_open``: whether the panel is shown (starts False).
- ``larry_history``: list of (question, AssistantResponse); survives close/reopen. In memory only
  (never written to disk); obvious personal info is redacted before it is stored.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import streamlit as st

from reslink.assistant import recent_history
from reslink.models import AssistantResponse
from reslink.privacy import redact
from reslink.ui import render_response

WELCOME_MESSAGE = (
    "Hey! I'm Larry, your ResLink AI assistant! Need help finding an RA resource, "
    "understanding housing policies, or accessing a portal? Just ask!"
)
LOADING_MESSAGE = "Larry is checking verified resources..."
INPUT_PLACEHOLDER = "Ask Larry a question (no resident names or IDs)..."
ICON = ":material/chat:"

OPEN_KEY = "larry_open"
HISTORY_KEY = "larry_history"

_CSS_PATH = Path(__file__).parent / "static" / "larry.css"

# ask(question, history): history = recent (question, answer) pairs, used only to resolve
# follow-up references (see reslink.assistant.recent_history / sanitize_history).
Ask = Callable[[str, list], AssistantResponse]


def _init_state() -> None:
    st.session_state.setdefault(OPEN_KEY, False)
    st.session_state.setdefault(HISTORY_KEY, [])


def _open() -> None:
    st.session_state[OPEN_KEY] = True


def _inject_css() -> None:
    st.html(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>")


def _render_exchange(question: str, response: AssistantResponse) -> None:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant", avatar=ICON):
        render_response(response)


@st.fragment
def _render_panel(ask: Ask) -> None:
    """The open chat window. A fragment: sending a message reruns only this panel."""
    with st.container(key="larry-panel"):
        with st.container(key="larry-header", horizontal=True, vertical_alignment="center"):
            st.markdown("**Larry**  \nResLink AI Assistant", width="stretch")
            if st.button("", icon=":material/close:", key="larry_close", help="Minimize Larry"):
                st.session_state[OPEN_KEY] = False
                st.rerun(scope="app")  # full rerun so the launcher replaces the panel

        messages = st.container(key="larry-messages", height=440, autoscroll=True)
        # Placed after the messages area so it stays at the bottom of the panel.
        # submit_mode="disable" blocks duplicate submissions while an answer is generated.
        question = st.chat_input(INPUT_PLACEHOLDER, key="larry_input", submit_mode="disable")

        with messages:
            with st.chat_message("assistant", avatar=ICON):
                st.write(WELCOME_MESSAGE)
            for past_question, past_response in st.session_state[HISTORY_KEY]:
                _render_exchange(past_question, past_response)
            if question:
                # Obvious personal info is never displayed back or kept in session history.
                shown = redact(question)
                with st.chat_message("user"):
                    st.write(shown)
                with st.chat_message("assistant", avatar=ICON):
                    with st.spinner(LOADING_MESSAGE):
                        # Last 2 usable exchanges (privacy-blocked turns excluded); the
                        # assistant re-sanitizes them before anything reaches Gemini.
                        response = ask(question, recent_history(st.session_state[HISTORY_KEY]))
                    render_response(response)
                st.session_state[HISTORY_KEY].append((shown, response))


def render_larry(ask: Ask) -> None:
    """Render the launcher (closed) or the chat panel (open). Call once, at the end of app.py."""
    _init_state()
    _inject_css()
    if st.session_state[OPEN_KEY]:
        _render_panel(ask)
    else:
        with st.container(key="larry-launcher"):
            st.button("Larry", icon=ICON, key="larry_launch", type="primary", on_click=_open,
                      help="Chat with Larry, the ResLink AI assistant")
