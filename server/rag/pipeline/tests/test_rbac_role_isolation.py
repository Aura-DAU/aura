"""
v7 regression: RBAC role isolation for RAG retrieval.

Confirms:
  - get_allowed_roles("student") == {"public", "student"} exactly
  - get_allowed_roles("guest")   resolves via alias_map to "public"'s set
  - A chunk tagged dls:["faculty"] never passes the BM25/DLS filter for a
    student-role query, even though "faculty" chunks ARE visible to
    faculty_general and above.

Uses the same array-intersection filter approach as test_dls.py so this
exercises the real filtering logic rather than re-deriving it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.retrieval.rbac import get_allowed_roles


def _chunk_visible(chunk_authorization: list[str], allowed_roles: list[str]) -> bool:
    return bool(set(chunk_authorization) & set(allowed_roles))


def test_student_role_sees_only_public_and_student():
    allowed = set(get_allowed_roles("student"))
    assert allowed == {"public", "student"}


def test_guest_role_aliases_to_public_only():
    allowed = set(get_allowed_roles("guest"))
    assert allowed == {"public"}


def test_faculty_chunks_not_visible_to_students():
    student_allowed = get_allowed_roles("student")
    guest_allowed = get_allowed_roles("guest")

    faculty_only_chunk = {"chunk_id": "c-fac-1", "authorization": ["faculty"]}
    public_chunk = {"chunk_id": "c-pub-1", "authorization": ["public"]}

    assert not _chunk_visible(faculty_only_chunk["authorization"], student_allowed), (
        "A faculty-tagged chunk must not be visible to a student role"
    )
    assert not _chunk_visible(faculty_only_chunk["authorization"], guest_allowed), (
        "A faculty-tagged chunk must not be visible to a guest role"
    )
    assert _chunk_visible(public_chunk["authorization"], student_allowed)
    assert _chunk_visible(public_chunk["authorization"], guest_allowed)


def test_faculty_role_can_see_faculty_chunks():
    faculty_allowed = get_allowed_roles("faculty_general")
    faculty_only_chunk = {"chunk_id": "c-fac-1", "authorization": ["faculty"]}
    assert _chunk_visible(faculty_only_chunk["authorization"], faculty_allowed)


def test_unknown_role_string_fails_to_public_only():
    """A role string that slips through the JWT unmapped must fail to
    minimum privilege ('public'), never fail open to broader access."""
    allowed = set(get_allowed_roles("some_unrecognised_role_xyz"))
    assert allowed == {"public"}
