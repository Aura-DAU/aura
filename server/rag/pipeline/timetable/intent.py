"""
intent.py -- fast, dependency-free detector for timetable-related queries.

Why this exists
================
`personal_query_classifier.PersonalQueryClassifier` is an LLM call and its
`erp_fields` enum never included "timetable" (timetable is AURA-owned data
in PostgreSQL, not an ERP field) -- so timetable questions previously fell
through to the generic ERP-context path in aura_chat_graph.py, which has no
handler for them at all, and the student got either a hallucinated or an
empty answer.

This module is a cheap, synchronous, regex/keyword classifier that runs
before the LLM classifier and catches the overwhelming majority of real
timetable phrasing (English and common Hinglish variants) without an extra
network round-trip. It deliberately errs toward matching -- a false
positive here just means the query goes through the timetable tool-calling
orchestrator instead of general RAG, and that orchestrator's own system
prompt tells the model to say plainly if no tool can answer the question.
"""

import re

_TIMETABLE_PATTERNS = [
    r"\btime\s*-?\s*table\b",
    r"\bschedule\b",
    r"\b(my|today'?s?|tomorrow'?s?|next|upcoming)\s+class(es)?\b",
    r"\bclass(es)?\s+(today|tomorrow|kab|when)\b",
    r"\bwhat.{0,15}class(es)?\b",
    r"\bwhich\s+class(es)?\b",
    r"\belective(s)?\b",
    r"\b(lecture|lab|tutorial)s?\s+(today|tomorrow|schedule|timing)\b",
    r"\b(add|remove|move|change|shift|update|edit)\b.{0,30}\b(class|lecture|lab|tutorial|timetable|schedule)\b",
    r"\b(section|sec)\s*[- ]?\s*[a-z0-9]\b.{0,15}\b(change|update|set|switch)\b",
    r"\b(change|update|set|switch)\b.{0,15}\b(section|sec)\b",
    r"\bsync\b.{0,20}\bcalendar\b",
    r"\bgoogle\s+calendar\b",
    r"\bteaching\s+schedule\b",
    r"\bfree\s+period\b",
    r"\bwhen\s+is\s+my\s+(next\s+)?class\b",
    r"\bundo\b.{0,20}\b(timetable|class|schedule)\b",
]

_TIMETABLE_RE = re.compile("|".join(_TIMETABLE_PATTERNS), re.IGNORECASE)


def is_timetable_query(query: str) -> bool:
    """Returns True if `query` is very likely about a student's/faculty's
    own timetable, schedule, electives, section, or a change to any of
    those -- cheap enough to call on every request before the (slower,
    LLM-based) PersonalQueryClassifier runs."""
    if not query or not isinstance(query, str):
        return False
    return bool(_TIMETABLE_RE.search(query))
