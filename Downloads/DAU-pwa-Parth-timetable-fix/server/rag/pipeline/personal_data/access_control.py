# Central authorization policy. Every personal-data tool handler — in
# ecampus/tool_registry.py and anywhere else — must call
# privacy incident.

# Roles that are treated as elevated (non-student) and are allowed to
# query a target student's data (subject to the consent gate in
# composite_tools.py). This list mirrors the full 12-role hierarchy in
# server/rag/access_control.py — update both if new roles are added.
_ELEVATED_ROLES = {
    "faculty",
    "faculty_coord",
    "faculty_convenor_ug",
    "faculty_convenor_pg",
    "dean_students",
    "dean_faculty",
    "dean_academic",
    "registrar",
    "admin_staff",
    "admin",
    "superadmin",
}


from typing import Optional


class AccessDenied(Exception):
    pass


def authorize_personal_query(identity: dict, target_student_id: Optional[str]) -> str:
    # identity: {"role": str, "erp_id": str, "department": str|None}
    # target_student_id: the student the query is ABOUT. None means
    # Returns the ERP student_id that's safe to query, or raises AccessDenied.
    if not identity or "role" not in identity or "erp_id" not in identity:
        raise AccessDenied("Missing or incomplete identity — cannot authorize.")

    role = identity["role"]
    requester_id = identity["erp_id"]

    if role == "student":
        if target_student_id is not None and target_student_id != requester_id:
            raise AccessDenied("Students may only access their own academic data.")
        return requester_id

    if role in _ELEVATED_ROLES:
        if target_student_id is None:
            raise AccessDenied(
                f"Role '{role}' must specify which student's data they need."
            )
        if target_student_id == requester_id:
            raise AccessDenied(
                f"Requester erp_id cannot itself be used as a student record."
            )
        # NOTE (eCampus scraping model specifically): under the per-student
        # credential vault, AURA only ever holds ONE person's eCampus login
        # at a time. There is no legitimate way for an elevated-role member's
        # request to use a STUDENT's stored credentials to scrape that
        # student's own portal — they never possess that student's password,
        # nor should AURA pretend otherwise.
        #
        # Faculty/elevated access to a student's data, under this credential
        # model, can only be authorized when the STUDENT has explicitly
        # opted in (see ecampus/credentials_vault.py:
        # grant_advisor_consent / has_advisor_consent). Elevated roles cannot
        # be authorized here on enrollment/advising status alone — consent is
        # an additional, separate gate checked by the calling tool handler
        # (see ecampus/composite_tools.py:get_advisee_snapshot).
        return target_student_id

    raise AccessDenied(f"Unrecognized role: {role!r}")

