"""
Tool registry — all handlers call ERPConnector directly (SQL-only).

No eCampus client, no credentials vault, no write tools.
Every personal-data tool still goes through AccessControlGate before
touching the ERP connector, and every access is audit-logged.

Removed tools (DB/scraper no longer available):
  - get_attendance           (no DB table access granted)
  - check_exam_eligibility   (depended on attendance)
  - refresh_my_data          (write tool — AURA is read-only)
  - share_data_with_advisor  (write tool)
  - revoke_advisor_access    (write tool)

Moved (not removed):
  - get_timetable            -> pipeline.timetable.tool_registry.get_my_timetable
                                 (timetable is AURA-owned data, not ERP-sourced,
                                 and now supports per-student edits — see that
                                 module's docstring)
"""

from dataclasses import dataclass
from typing import Callable
from erp_connector import ERPConnector
from . import composite_tools
from . import faculty_workflow_tools
from . import student_workflow_tools
from . import community_tools
from . import scholarship_tools
from ..personal_data.access_control import authorize_personal_query, AccessDenied
from ..personal_data.audit import audit_log

_erp = ERPConnector()


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    category: str             # "read" | "derived"
    allowed_roles: list[str]
    handler: Callable


# ── Handlers ──────────────────────────────────────────────────────────────

def _handle_get_student_detail(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_student_profile(roll)
    audit_log(identity, query="get_student_detail", allowed=True, target=roll)
    return data or {"error": "Profile not found."}


def _handle_get_registration_status(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_registration(roll)
    audit_log(identity, query="get_registration_status", allowed=True, target=roll)
    return {"courses": data}


def _handle_get_course_adjustments(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_course_adjustments(roll)
    audit_log(identity, query="get_course_adjustments", allowed=True, target=roll)
    return {"adjustments": data}


def _handle_get_result(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_grades(roll)
    audit_log(identity, query="get_result", allowed=True, target=roll)
    return {"grades": data}


def _handle_get_cgpa(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_cgpa(roll)
    audit_log(identity, query="get_cgpa", allowed=True, target=roll)
    return data or {"error": "CGPA not found."}


def _handle_get_hostel_info(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_hostel(roll)
    audit_log(identity, query="get_hostel_info", allowed=True, target=roll)
    return data or {"error": "No hostel allocation found."}


def _handle_get_fees_status(identity, **kwargs):
    roll = authorize_personal_query(identity, kwargs.get("student_id"))
    data = _erp.get_fees(roll)
    audit_log(identity, query="get_fees_status", allowed=True, target=roll)
    return data or {"error": "Fee record not found."}


def _handle_get_faculty_schedule(identity, **kwargs):
    if identity["role"] not in ("faculty", "faculty_general", "faculty_coord",
                                "faculty_convenor_ug", "faculty_convenor_pg",
                                "dean_faculty", "dean_academic", "superadmin"):
        raise AccessDenied("Only faculty may request a faculty teaching schedule.")
    erp_id = identity.get("erp_id")
    if not erp_id:
        raise AccessDenied("Faculty ERP ID not found in identity.")
    data = _erp.get_faculty_teaching_schedule(erp_id)
    audit_log(identity, query="get_faculty_schedule", allowed=True, target=erp_id)
    return {"schedule": data}


# ── Tool definitions ───────────────────────────────────────────────────────

GET_STUDENT_DETAIL = Tool(
    name="get_student_detail",
    description="Get the requester's own name, roll number, program, and batch from the ERP database.",
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
    description="Get the requester's semester-wise grades from the ERP database.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_result,
)

GET_CGPA = Tool(
    name="get_cgpa",
    description="Get the requester's current CGPA from the ERP database.",
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
    description="Get the requester's fee payment status and dues from the ERP database.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_fees_status,
)

GET_FACULTY_SCHEDULE = Tool(
    name="get_faculty_schedule",
    description="Get the requesting faculty member's weekly teaching schedule directly from the ERP database.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["faculty"], handler=_handle_get_faculty_schedule,
)

GET_ACADEMIC_SNAPSHOT = Tool(
    name="get_academic_snapshot",
    description=(
        "Get a combined view of the requester's CGPA, grades, fees, hostel, and "
        "registered courses. Use this instead of calling several individual tools "
        "when the user wants a general status check."
    ),
    parameters={"type": "object", "properties": {}},
    category="derived", allowed_roles=["student"],
    handler=composite_tools.get_academic_snapshot,
)

COMPARE_SEMESTER_TREND = Tool(
    name="compare_semester_trend",
    description="Get a breakdown of the requester's courses and grades grouped by semester.",
    parameters={"type": "object", "properties": {}},
    category="derived", allowed_roles=["student"],
    handler=composite_tools.compare_semester_trend,
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
    description=(
        "Get a specific student's academic snapshot — only works if that student "
        "has explicitly shared their data with the requesting faculty member through AURA."
    ),
    parameters={
        "type": "object",
        "properties": {"student_erp_id": {"type": "string"}},
        "required": ["student_erp_id"],
    },
    category="read", allowed_roles=["faculty"],
    handler=composite_tools.get_advisee_snapshot,
)


# ── Advisory tools (no ERP writes, no ticketing writes) ─────────────────────

LEAVE_APPLICATION_GUIDANCE = Tool(
    name="leave_application_guidance",
    description="Get an advisory eligibility/document/approval checklist for a faculty leave application, from KB policy.",
    parameters={"type": "object", "properties": {"leave_type": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_leave_application_guidance,
)

CPDA_TRAVEL_APPROVAL_GUIDANCE = Tool(
    name="cpda_travel_approval_guidance",
    description="Get an advisory checklist for CPDA / conference travel approval, from KB policy.",
    parameters={"type": "object", "properties": {"purpose": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_cpda_travel_approval_guidance,
)

SEED_GRANT_GUIDANCE = Tool(
    name="seed_grant_guidance",
    description="Get advisory eligibility, proposal structure, deadlines, and reporting obligations for a seed grant, from KB policy.",
    parameters={"type": "object", "properties": {"research_area": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_seed_grant_guidance,
)

CERTIFICATE_REQUEST_GUIDANCE = Tool(
    name="certificate_request_guidance",
    description="Get a step-by-step checklist for requesting a bonafide certificate, transcript, or ID card, from KB policy.",
    parameters={"type": "object", "properties": {"document_type": {"type": "string"}}},
    category="read", allowed_roles=["student"],
    handler=student_workflow_tools.handle_certificate_request_guidance,
)

HOSTEL_COMPLAINT_GUIDANCE = Tool(
    name="hostel_complaint_guidance",
    description="Summarize a hostel complaint and provide the correct contact. Does not file a ticket.",
    parameters={
        "type": "object",
        "properties": {"complaint_type": {"type": "string"}, "complaint_detail": {"type": "string"}},
    },
    category="read", allowed_roles=["student"],
    handler=student_workflow_tools.handle_hostel_complaint_guidance,
)

EVENT_CLUB_REGISTRATION_GUIDANCE = Tool(
    name="event_club_registration_guidance",
    description="Get the membership/registration process and convenor contact for a named club or event.",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    category="read", allowed_roles=["student"],
    handler=community_tools.handle_event_club_registration_guidance,
)

FACULTY_COMMITTEE_RESPONSIBILITIES = Tool(
    name="faculty_committee_responsibilities",
    description="Get the Terms of Reference summary (mandate, composition, responsibilities) for a named faculty committee.",
    parameters={"type": "object", "properties": {"committee_name": {"type": "string"}}, "required": ["committee_name"]},
    category="read", allowed_roles=["faculty"],
    handler=community_tools.handle_faculty_committee_responsibilities,
)

SCREEN_SCHOLARSHIP_ELIGIBILITY = Tool(
    name="screen_scholarship_eligibility",
    description=(
        "Cross-references the requester's own academic profile (branch, year, category, "
        "cgpa, annual_income) against university scholarship/financial-aid rules in the KB "
        "to check eligibility and return application requirements. Guidance only — no "
        "application is submitted."
    ),
    parameters={
        "type": "object",
        "properties": {
            "branch": {"type": "string", "description": "Branch/program of study (e.g. BTech ICT, MSc, BS+MS)."},
            "year": {"type": "integer", "description": "Current year of study (1, 2, 3, 4)."},
            "category": {"type": "string", "description": "Admission category (General, SC/ST, DAFS, NRI, etc.)."},
            "cgpa": {"type": "number", "description": "Current CGPA or CPI."},
            "annual_income": {"type": "number", "description": "Annual family income in INR (optional)."},
        },
        "required": ["branch", "year", "category", "cgpa"],
    },
    category="read", allowed_roles=["student"],
    handler=scholarship_tools.screen_scholarship_eligibility,
)

UPDATE_TRACKING_FLAGS = Tool(
    name="update_tracking_flags",
    description="Updates the user's persistent personal profile facts (e.g., DOB, age, interests) shared conversationally.",
    parameters={
        "type": "object",
        "properties": {
            "facts": {
                "type": "object", 
                "description": "A dictionary of key-value pairs representing the user's personal facts to track (e.g., {'dob': '1999-05-12', 'age': 25})"
            }
        },
        "required": ["facts"]
    },
    category="write", allowed_roles=["student", "guest", "faculty", "admin"],
    handler=student_workflow_tools.handle_update_tracking_flags,
)


TOOL_REGISTRY: dict[str, Tool] = {
    t.name: t for t in [
        GET_STUDENT_DETAIL, GET_REGISTRATION_STATUS, GET_COURSE_ADJUSTMENTS,
        GET_RESULT, GET_CGPA, GET_HOSTEL_INFO, GET_FEES_STATUS,
        GET_FACULTY_SCHEDULE,
        GET_ACADEMIC_SNAPSHOT, COMPARE_SEMESTER_TREND,
        LIST_MY_DATA_SHARING, GET_ADVISEE_SNAPSHOT,
        LEAVE_APPLICATION_GUIDANCE, CPDA_TRAVEL_APPROVAL_GUIDANCE, SEED_GRANT_GUIDANCE,
        CERTIFICATE_REQUEST_GUIDANCE, HOSTEL_COMPLAINT_GUIDANCE,
        EVENT_CLUB_REGISTRATION_GUIDANCE, FACULTY_COMMITTEE_RESPONSIBILITIES,
        SCREEN_SCHOLARSHIP_ELIGIBILITY, UPDATE_TRACKING_FLAGS,
    ]
}


def tools_for_role(role: str) -> list[Tool]:
    return [t for t in TOOL_REGISTRY.values() if role in t.allowed_roles]
