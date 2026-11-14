"""Lightweight check for obvious personal information in a user's message.

Runs before retrieval and before anything is sent to Gemini. It only recognizes a few
unambiguous patterns (9-digit ID numbers, SSN-shaped numbers, email addresses, phone numbers).
It is NOT comprehensive: names, room numbers, birthdays written in words, NetIDs, and
free-text descriptions of residents are not detected.
"""

from __future__ import annotations

import re

PATTERNS: dict[str, re.Pattern] = {
    "an email address": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "an SSN-like number": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    "a phone number": re.compile(r"(?<![\d-])(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\d-])|(?<!\d)\d{10}(?!\d)"),
    "a 9-digit ID number": re.compile(r"(?<!\d)\d{9}(?!\d)"),
}


def detect_personal_info(text: str) -> list[str]:
    """Kinds of obvious personal information found in ``text`` (empty list if none)."""
    return [kind for kind, pattern in PATTERNS.items() if pattern.search(text)]


def redact(text: str) -> str:
    """Replace detected patterns with placeholders, e.g. for display in chat history."""
    for kind, pattern in PATTERNS.items():
        text = pattern.sub(f"[{kind.split(' ', 1)[1]} removed]", text)
    return text
