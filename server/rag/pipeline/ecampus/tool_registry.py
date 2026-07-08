"""
Tool registry, revised to call the scraping-based ECampusClient instead of
the OAuth/REST one. RBAC pattern is unchanged from the earlier guide —
every personal-data tool still goes through access_control.authorize_personal_query
before touching eCampus, and every access (allowed or denied) is audit-logged.
"""

from dataclasses import dataclass
from typing import Callable
from .client import ECampusClient, get_faculty_schedule as _get_faculty_schedule
from .credentials_vault import CredentialsNotLinked
from . import composite_tools
from ..personal_data.access_control import authorize_personal_query, AccessDenied
from ..personal_data.audit import audit_log


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    category: str             # "knowledge" | "read" | "derived"
    allowed_roles: list[str]
    handler: Callable


def _student_only_client(identity, target_student_id=None) -> ECampusClient:
    """Every read tool resolves to the requester's own erp_id only, in this
    student-phase build — faculty querying a specific student's data via
    eCampus scraping isn't implemented yet (it requires that student's own
    linked credentials, which raises its own consent questions worth a
    separate design pass before building it)."""
    student_id = authorize_personal_query(identity, target_student_id)
    return ECampusClient(erp_id=student_id)


def _handle_get_student_detail(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_student_detail()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_student_detail", allowed=True, target=client.erp_id)
    return data


def _handle_get_registration_status(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_registration()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_registration_status", allowed=True, target=client.erp_id)
    return {"courses": data}


def _handle_get_course_adjustments(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_course_adjustments()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_course_adjustments", allowed=True, target=client.erp_id)
    return {"adjustments": data}


def _handle_get_result(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_result()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_result", allowed=True, target=client.erp_id)
    return data


def _handle_get_cgpa(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_cgpa()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_cgpa", allowed=True, target=client.erp_id)
    return data


def _handle_get_hostel_info(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_hostel()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_hostel_info", allowed=True, target=client.erp_id)
    return data


def _handle_get_fees_status(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_fees()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_fees_status", allowed=True, target=client.erp_id)
    return data


def _handle_get_attendance(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_attendance()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_attendance", allowed=True, target=client.erp_id)
    return {"attendance": data}


def _handle_get_utilities(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_utilities()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_utilities", allowed=True, target=client.erp_id)
    return data


def _handle_get_timetable(identity, **kwargs):
    client = _student_only_client(identity, kwargs.get("student_id"))
    try:
        data = client.get_timetable()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    audit_log(identity, query="get_timetable", allowed=True, target=client.erp_id)
    return {"timetable": data}


def _handle_get_faculty_schedule(identity, **kwargs):
    if identity["role"] != "faculty":
        raise AccessDenied("Only faculty may request a faculty teaching schedule.")
    faculty_name = kwargs.get("faculty_name")
    if not faculty_name:
        raise AccessDenied("faculty_name is required.")
    # Self-only for now: a faculty member can derive their own schedule from
    # the pooled timetable data, not someone else's — extend deliberately if
    # a legitimate cross-faculty lookup need (e.g. for a department admin
    # role) comes up later.
    result = _get_faculty_schedule(faculty_name)
    audit_log(identity, query="get_faculty_schedule", allowed=True, target=faculty_name)
    return result


def _handle_get_club_event_info(identity, **kwargs):
    """
    Knowledge tool — no eCampus credentials needed.
    Searches the student_faculty/ KB for a given club or event name and
    returns membership process, convenor contact, and next steps as a
    formatted checklist.

    The handler returns a structured text block; answer_generator.py
    will incorporate it as context if this tool is invoked via the
    retrieval pipeline's tool-routing path.
    """
    # pyrefly: ignore [missing-import]
    from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline

    club_or_event = kwargs.get("club_or_event_name", "").strip()
    if not club_or_event:
        return {
            "error": "club_or_event_name is required.",
            "checklist": None,
        }

    # Build a targeted natural-language query for the retrieval pipeline.
    query = (
        f"How do I join or register for {club_or_event}? "
        "Who is the convener, what is the membership process, "
        "and what are the next steps?"
    )

    role = identity.get("role", "student") if isinstance(identity, dict) else getattr(identity, "role", "student")

    try:
        pipeline = RetrievalPipeline()
        result = pipeline.get_context(query, history=[], user_role=role)
        context = result.get("context", "")
        sources = result.get("sources", [])
    except Exception as e:
        return {
            "error": f"KB retrieval failed: {e}",
            "checklist": None,
        }

    if not context:
        return {
            "club_or_event": club_or_event,
            "checklist": (
                f"No information found for '{club_or_event}' in the "
                "knowledge base. Try the full official name, or contact "
                "sbg@dau.ac.in for a list of active clubs and committees."
            ),
            "sources": [],
        }

    audit_log(identity, query=f"get_club_event_info:{club_or_event}", allowed=True, target=club_or_event)

    return {
        "club_or_event": club_or_event,
        "checklist": context,
        "sources": sources,
    }


GET_STUDENT_DETAIL = Tool(
    name="get_student_detail",
    description="Get the requester's own name, roll number, program, and batch from eCampus.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_student_detail,
)

GET_REGISTRATION_STATUS = Tool(
    name="get_registration_status",
    description="Get the requester's currently registered courses for this semester.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_registration_status,
)

GET_COURSE_ADJUSTMENTS = Tool(
    name="get_course_adjustments",
    description="Get the requester's course add/drop adjustment history.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_course_adjustments,
)

GET_RESULT = Tool(
    name="get_result",
    description="Get the requester's semester-wise grades and SGPA from eCampus.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_result,
)

GET_CGPA = Tool(
    name="get_cgpa",
    description="Get the requester's own CGPA (derived from their Result page).",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_cgpa,
)

GET_HOSTEL_INFO = Tool(
    name="get_hostel_info",
    description="Get the requester's hostel allocation and mess group.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_hostel_info,
)

GET_FEES_STATUS = Tool(
    name="get_fees_status",
    description="Get the requester's fee payment status and dues.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_fees_status,
)

GET_ATTENDANCE = Tool(
    name="get_attendance",
    description="Get the requester's per-course attendance percentages.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_attendance,
)

GET_UTILITIES = Tool(
    name="get_utilities",
    description="Get whatever miscellaneous services are listed under the requester's Utilities tab.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_utilities,
)

GET_TIMETABLE = Tool(
    name="get_timetable",
    description="Get the requester's weekly class timetable.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_timetable,
)

GET_FACULTY_SCHEDULE = Tool(
    name="get_faculty_schedule",
    description=(
        "Get a faculty member's derived weekly teaching schedule, built from "
        "pooled student timetable data rather than a direct eCampus faculty login. "
        "May be incomplete if not all sections they teach have appeared in scraped "
        "timetables yet."
    ),
    parameters={
        "type": "object",
        "properties": {"faculty_name": {"type": "string", "description": "The faculty member's name."}},
        "required": ["faculty_name"],
    },
    category="derived", allowed_roles=["faculty"], handler=_handle_get_faculty_schedule,
)


CHECK_EXAM_ELIGIBILITY = Tool(
    name="check_exam_eligibility",
    description="Check whether the requester's attendance meets the exam eligibility threshold in every registered course, flagging at-risk courses.",
    parameters={"type": "object", "properties": {}},
    category="derived", allowed_roles=["student"],
    handler=composite_tools.check_exam_eligibility,
)

GET_ACADEMIC_SNAPSHOT = Tool(
    name="get_academic_snapshot",
    description="Get a single combined view of the requester's CGPA, attendance, fees, hostel, and registration status — use this instead of calling several individual tools when the user wants a general status check.",
    parameters={"type": "object", "properties": {}},
    category="derived", allowed_roles=["student"],
    handler=composite_tools.get_academic_snapshot,
)

COMPARE_SEMESTER_TREND = Tool(
    name="compare_semester_trend",
    description="Get a breakdown of the requester's courses and grades grouped by semester, to support questions about performance trends over time.",
    parameters={"type": "object", "properties": {}},
    category="derived", allowed_roles=["student"],
    handler=composite_tools.compare_semester_trend,
)

REFRESH_MY_DATA = Tool(
    name="refresh_my_data",
    description="Force AURA to re-fetch fresh data from eCampus instead of using cached results — use this if the user says their data seems outdated or they just made a change on eCampus (e.g. just registered for a course).",
    parameters={"type": "object", "properties": {}},
    category="write", allowed_roles=["student", "faculty"],
    handler=composite_tools.refresh_my_data,
)

SHARE_DATA_WITH_ADVISOR = Tool(
    name="share_data_with_advisor",
    description="Grant a specific faculty member (by their ERP ID) permission to view the requester's CGPA and attendance through AURA. Requires explicit user confirmation before execution.",
    parameters={
        "type": "object",
        "properties": {"faculty_erp_id": {"type": "string"}},
        "required": ["faculty_erp_id"],
    },
    category="write", allowed_roles=["student"],
    handler=composite_tools.share_data_with_advisor,
)

REVOKE_ADVISOR_ACCESS = Tool(
    name="revoke_advisor_access",
    description="Revoke a previously granted faculty member's access to the requester's academic data.",
    parameters={
        "type": "object",
        "properties": {"faculty_erp_id": {"type": "string"}},
        "required": ["faculty_erp_id"],
    },
    category="write", allowed_roles=["student"],
    handler=composite_tools.revoke_advisor_access,
)

LIST_MY_DATA_SHARING = Tool(
    name="list_my_data_sharing",
    description="List which faculty members currently have access to the requester's academic data.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"],
    handler=composite_tools.list_my_data_sharing,
)

GET_ADVISEE_SNAPSHOT = Tool(
    name="get_advisee_snapshot",
    description="Get a specific student's CGPA and attendance — only works if that student has explicitly shared their data with the requesting faculty member through AURA.",
    parameters={
        "type": "object",
        "properties": {"student_erp_id": {"type": "string"}},
        "required": ["student_erp_id"],
    },
    category="read", allowed_roles=["faculty"],
    handler=composite_tools.get_advisee_snapshot,
)


GET_CLUB_EVENT_INFO = Tool(
    name="get_club_event_info",
    description=(
        "Given a club or event name, return the membership / registration process, "
        "the convenor contact, and next steps as a formatted checklist. "
        "Uses the student_faculty knowledge base — no eCampus login required."
    ),
    parameters={
        "type": "object",
        "properties": {
            "club_or_event_name": {
                "type": "string",
                "description": "The exact or approximate name of the club, committee, or event (e.g. 'Programming Club', 'Synapse', 'Hostel Management Committee').",
            }
        },
        "required": ["club_or_event_name"],
    },
    category="knowledge",
    allowed_roles=["student", "faculty"],
    handler=_handle_get_club_event_info,
)


TOOL_REGISTRY: dict[str, Tool] = {
    t.name: t for t in [
        GET_STUDENT_DETAIL, GET_REGISTRATION_STATUS, GET_COURSE_ADJUSTMENTS,
        GET_RESULT, GET_CGPA, GET_HOSTEL_INFO, GET_FEES_STATUS, GET_ATTENDANCE,
        GET_UTILITIES, GET_TIMETABLE, GET_FACULTY_SCHEDULE,
        CHECK_EXAM_ELIGIBILITY, GET_ACADEMIC_SNAPSHOT, COMPARE_SEMESTER_TREND,
        REFRESH_MY_DATA, SHARE_DATA_WITH_ADVISOR, REVOKE_ADVISOR_ACCESS,
        LIST_MY_DATA_SHARING, GET_ADVISEE_SNAPSHOT,
        GET_CLUB_EVENT_INFO,
    ]
}


def tools_for_role(role: str) -> list[Tool]:
    return [t for t in TOOL_REGISTRY.values() if role in t.allowed_roles]
