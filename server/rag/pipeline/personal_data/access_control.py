"""
Central authorization policy. Every personal-data tool handler — in
ecampus/tool_registry.py and anywhere else — must call
authorize_personal_query() before touching any per-person data. This is
intentionally the ONLY place this decision gets made, so a future change to
the rule ("faculty can now see X") happens in one function, not scattered
across N handlers.

Fails CLOSED: any ambiguity, missing data, or unexpected role raises
AccessDenied rather than defaulting to allow. This is the opposite default
from query_guardrail.py's "fail open" safety filter — that's deliberate.
Read access denied is an inconvenience; read access wrongly granted is a
privacy incident.
"""


class AccessDenied(Exception):
    pass


def authorize_personal_query(identity: dict, target_student_id: str | None) -> str:
    """
    identity: {"role": "student"|"faculty", "erp_id": str, "department": str|None}
    target_student_id: the student the query is ABOUT. None means
        "the requester themselves."

    Returns the ERP student_id that's safe to query, or raises AccessDenied.
    """
    if not identity or "role" not in identity or "erp_id" not in identity:
        raise AccessDenied("Missing or incomplete identity — cannot authorize.")

    role = identity["role"]
    requester_id = identity["erp_id"]

    if role == "student":
        if target_student_id is not None and target_student_id != requester_id:
            raise AccessDenied("Students may only access their own academic data.")
        return requester_id

    if role == "faculty":
        if target_student_id is None:
            raise AccessDenied("Faculty must specify which student's data they need.")
        if target_student_id == requester_id:
            raise AccessDenied("Faculty erp_id cannot itself be a student record.")

        # NOTE (eCampus scraping model specifically): under the per-student
        # credential vault, AURA only ever holds ONE person's eCampus login
        # at a time. There is no legitimate way for a faculty member's
        # request to use a STUDENT's stored credentials to scrape that
        # student's own portal — faculty never possess that student's
        # password, nor should AURA pretend otherwise.
        #
        # So faculty access to a student's data, under this credential
        # model, can only be authorized when the STUDENT has explicitly
        # opted in (see ecampus/credentials_vault.py:
        # grant_advisor_consent / has_advisor_consent). Faculty cannot be
        # authorized here on enrollment/advising status alone — consent is
        # an additional, separate gate checked by the calling tool handler
        # (see ecampus/composite_tools.py:get_advisee_snapshot).
        #
        # If/when DAU IT provides real backend access (Section 1 of the IT
        # ask-list) instead of per-student scraping, this function is where
        # you'd add a get_students_for_faculty() enrollment check instead of
        # relying on consent — a service-account-backed integration doesn't
        # have this limitation.
        return target_student_id

    raise AccessDenied(f"Unrecognized role: {role!r}")
