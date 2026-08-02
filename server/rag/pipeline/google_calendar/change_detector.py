"""
change_detector.py — Deterministic content hash for timetable slots.

Problem: Without change detection, every sync PATCHes every event even
when nothing changed. With 20+ recurring classes, that's 20+ unnecessary
API calls per sync — wasteful, slow, and burns Google Calendar API quota.

Solution: Compute a SHA-256 hash of each slot's mutable fields. Store
the hash in gcal_synced_events. On re-sync, compare the current hash with
the stored one — skip the PATCH call when they match.

Why SHA-256 truncated to 16 hex chars (64 bits)?
- Collision probability at 64 bits over millions of (erp_id, slot) pairs
  is negligible (~1 in 10^18). Good enough for an idempotency key.
- Keeps the column narrow (16 chars vs 64 chars for full SHA-256).
- Not a security hash — this is a content fingerprint, not a signature.

Fields hashed (all mutable fields that would change the Google event):
  course_code, course_name, day_of_week, start_time, end_time,
  room, faculty_name, session_type.

Fields deliberately NOT hashed:
  id (the slot's AURA primary key — this IS the slot_key, not content)
  sec (section — doesn't appear in the event body)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def slot_hash(slot: dict[str, Any]) -> str:
    """
    Return a 16-character hex content fingerprint of a timetable slot.

    Only fields that appear in the Google Calendar event body are included.
    This means slot_hash changes if and only if the event would look different
    to the student in Google Calendar.
    """
    fields = {
        "course_code":  slot.get("course_code") or "",
        "course_name":  slot.get("course_name") or "",
        "day_of_week":  slot.get("day_of_week"),
        "start_time":   slot.get("start_time") or "",
        "end_time":     slot.get("end_time") or "",
        "room":         slot.get("room") or "",
        "faculty_name": slot.get("faculty_name") or "",
        "session_type": slot.get("session_type") or "",
    }
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return digest[:16]


def slots_changed(new_hash: str, stored_hash: str | None) -> bool:
    """
    Returns True if the slot content has changed since it was last synced.
    If stored_hash is None (never synced), always returns True.
    """
    if stored_hash is None:
        return True
    return new_hash != stored_hash
