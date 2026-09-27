"""Pure helpers for a message that holds several questions.

A compound message is treated as a sequence of independent questions that are
routed to "lanes": deterministic tools (timetable), the student's own ERP
records, and document retrieval. Nothing is silently dropped: a question that
cannot be answered in this turn (guest asking for personal data, a second
person's records, off-topic) yields an explicit note instead.

No I/O and no LLM calls live here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

PERSONAL_TYPES = ("PERSONAL", "MIXED", "AGGREGATE")
RAG_TYPES = ("PUBLIC", "MIXED", "AGGREGATE")

_PUBLIC_DEFAULT = {"type": "PUBLIC", "target": None, "erp_fields": [], "intent": "RAG"}
_DATA_PERIOD_LINE_RE = re.compile(r"^\s*Data period:.*$", re.MULTILINE)


@dataclass
class Lanes:
    """Routing decision for one compound message."""

    classification: dict
    keep: list = field(default_factory=list)   # indices still to be answered
    rag: list = field(default_factory=list)    # indices that need documents
    notes: list = field(default_factory=list)  # fragments to prepend to the answer


def _target(classification: dict) -> str:
    return classification.get("target") or "self"


def _lane_key(classification: dict) -> tuple:
    return (_target(classification), classification.get("type") == "AGGREGATE")


def merge_classifications(
    questions: list,
    classifications: list,
    guest: bool = False,
    denial_text: str = "",
) -> Lanes:
    """Fold per-question classifier results into ONE classification.

    The ERP/access nodes evaluate a single (target, fields) request, so the
    first personal question defines the personal lane. A later personal
    question about a different person, or needing class-level aggregates
    instead of the user's own records, is deferred with an explicit note
    rather than answered with the wrong person's data.
    """
    n = len(questions)
    types = [(c or {}).get("type", "PUBLIC") for c in classifications]
    classifications = [c or dict(_PUBLIC_DEFAULT) for c in classifications]
    personal = [i for i, t in enumerate(types) if t in PERSONAL_TYPES]
    notes: list = []
    keep = list(range(n))

    if guest and personal:
        public = [i for i in keep if i not in personal]
        if not public:
            # Nothing answerable: the guest gate denies the whole message.
            return Lanes(classifications[personal[0]], keep, [], [])
        if denial_text:
            notes.append(denial_text)
        keep, personal = public, []

    if not personal:
        rag = [i for i in keep if types[i] in RAG_TYPES]
        return Lanes(dict(_PUBLIC_DEFAULT), keep, rag, notes)

    first = classifications[personal[0]]
    lane = [i for i in personal if _lane_key(classifications[i]) == _lane_key(first)]
    for i in personal:
        if i not in lane:
            notes.append(
                f'I can look up one person\'s (or one kind of) record per message, '
                f'so I have not answered "{questions[i]}" yet. Please ask it separately.'
            )
    keep = [i for i in keep if i in lane or i not in personal]

    fields: list = []
    for i in lane:
        for f in classifications[i].get("erp_fields") or []:
            if f not in fields:
                fields.append(f)

    rag = [i for i in keep if types[i] in RAG_TYPES]
    if first.get("type") == "AGGREGATE":
        merged_type = "AGGREGATE"
    elif rag:
        merged_type = "MIXED"
    else:
        merged_type = "PERSONAL"

    merged = {
        "type": merged_type,
        "target": first.get("target"),
        "erp_fields": fields,
        "intent": first.get("intent") or "PERSONAL",
    }
    return Lanes(merged, keep, rag, notes)


def compose_answer(prefix_parts: Optional[list], answer: Optional[str]) -> str:
    """Tool/denial fragments first (they were produced first), then the LLM answer."""
    parts = [p.strip() for p in (prefix_parts or []) if p and p.strip()]
    if answer and answer.strip():
        parts.append(answer.strip())
    return "\n\n".join(parts)


def merge_extras(target: dict, result: dict) -> dict:
    """Accumulate the non-text fields of a tool result (action_required,
    timetable_changed, is_personal_data) across several tool answers."""
    for key, value in (result or {}).items():
        if key in ("answer", "sources"):
            continue
        if isinstance(value, bool):
            target[key] = bool(target.get(key)) or value
        elif value:
            target[key] = value
    return target


def previous_assistant_answer(history: Optional[list], limit: int = 3500) -> str:
    """The most recent assistant turn, for "shorten/translate that" requests."""
    for turn in reversed(history or []):
        if not isinstance(turn, dict) or turn.get("role") != "assistant":
            continue
        content = _DATA_PERIOD_LINE_RE.sub("", str(turn.get("content") or "")).strip()
        if content:
            return content[:limit].rstrip() + (" ..." if len(content) > limit else "")
    return ""
