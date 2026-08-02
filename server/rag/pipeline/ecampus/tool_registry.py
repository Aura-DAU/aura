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
from . import academic_kb_tools
from . import admin_people_kb_tools
from . import research_careers_kb_tools
from . import campus_info_kb_tools
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
    description=(
        "Get an advisory eligibility/document/approval checklist for a faculty leave "
        "application, from KB policy. Prefer this over lookup_university_policy when "
        "the user is preparing their own leave application."
    ),
    parameters={"type": "object", "properties": {"leave_type": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_leave_application_guidance,
)

CPDA_TRAVEL_APPROVAL_GUIDANCE = Tool(
    name="cpda_travel_approval_guidance",
    description=(
        "Get an advisory checklist for CPDA / conference travel approval, from KB policy. "
        "Prefer this over lookup_research_info for personal CPDA process steps."
    ),
    parameters={"type": "object", "properties": {"purpose": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_cpda_travel_approval_guidance,
)

SEED_GRANT_GUIDANCE = Tool(
    name="seed_grant_guidance",
    description=(
        "Get advisory eligibility, proposal structure, deadlines, and reporting "
        "obligations for a seed grant, from KB policy. Prefer this over "
        "lookup_research_info for personal seed-grant application checklists."
    ),
    parameters={"type": "object", "properties": {"research_area": {"type": "string"}}},
    category="read", allowed_roles=["faculty"],
    handler=faculty_workflow_tools.handle_seed_grant_guidance,
)

CERTIFICATE_REQUEST_GUIDANCE = Tool(
    name="certificate_request_guidance",
    description=(
        "Get a step-by-step checklist for requesting a bonafide certificate, transcript, "
        "or ID card, from KB policy. Prefer this over lookup_student_services_info for "
        "document-request procedures."
    ),
    parameters={"type": "object", "properties": {"document_type": {"type": "string"}}},
    category="read", allowed_roles=["student"],
    handler=student_workflow_tools.handle_certificate_request_guidance,
)

HOSTEL_COMPLAINT_GUIDANCE = Tool(
    name="hostel_complaint_guidance",
    description=(
        "Summarize a hostel complaint and provide the correct contact. Does not file a "
        "ticket. Prefer this over lookup_campus_facilities / lookup_student_services_info "
        "when the user has a specific hostel complaint to route."
    ),
    parameters={
        "type": "object",
        "properties": {"complaint_type": {"type": "string"}, "complaint_detail": {"type": "string"}},
    },
    category="read", allowed_roles=["student"],
    handler=student_workflow_tools.handle_hostel_complaint_guidance,
)

SEARCH_STUDENT_CLUBS = Tool(
    name="search_student_clubs",
    description=(
        "Search or list STUDENT hobby clubs and SBG student committees matching an "
        "interest or keyword (e.g. music, coding, cultural, sports). Use for "
        "'what clubs exist' / 'clubs related to X'. Do NOT use for faculty "
        "governance ToR committees (Academic Council, BTP, Exam Committee) — "
        "use search_faculty_committees / faculty_committee_responsibilities instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Interest or keyword; omit or empty to list clubs broadly.",
            },
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=community_tools.handle_search_student_clubs,
)

GET_STUDENT_CLUB_INFO = Tool(
    name="get_student_club_info",
    description=(
        "Get purpose, who can join, convenor/faculty mentor/contact, and how to join "
        "for a named STUDENT club or SBG student committee (e.g. Programming Club, "
        "Cultural Committee, Music Club). Not for faculty governance ToR bodies."
    ),
    parameters={
        "type": "object",
        "properties": {"club_name": {"type": "string"}},
        "required": ["club_name"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=community_tools.handle_get_student_club_info,
)

GET_CLUB_MEMBERS = Tool(
    name="get_club_members",
    description=(
        "Get the published member roster (office-bearers and members with roles/"
        "student IDs when listed) for a named STUDENT club or SBG student committee "
        "from campus KB documents (SBG Club Committee Data / Core Members lists). "
        "Use when the user asks who is in a club, member lists, or roster. "
        "Does NOT query ERP personal records — only KB-published rosters. "
        "For convenor/email only, prefer lookup_club_office_bearers."
    ),
    parameters={
        "type": "object",
        "properties": {"club_name": {"type": "string"}},
        "required": ["club_name"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=community_tools.handle_get_club_members,
)

LOOKUP_CLUB_OFFICE_BEARERS = Tool(
    name="lookup_club_office_bearers",
    description=(
        "Look up Convenor, Dy. Convenor, faculty mentor, and club email for a named "
        "STUDENT club or SBG student committee from published SBG C_DCs / convenor "
        "sheets. Use for 'who is the convenor of X' / office-bearer contact questions. "
        "For a full member list use get_club_members. Not for faculty ToR committees."
    ),
    parameters={
        "type": "object",
        "properties": {"club_name": {"type": "string"}},
        "required": ["club_name"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=community_tools.handle_lookup_club_office_bearers,
)

EVENT_CLUB_REGISTRATION_GUIDANCE = Tool(
    name="event_club_registration_guidance",
    description=(
        "Get the step-by-step membership/registration process and convenor contact "
        "for a named STUDENT club or campus event. Use when the user asks how to "
        "join/register. For club purpose/overview use get_student_club_info; for "
        "who is in the club use get_club_members / lookup_club_office_bearers."
    ),
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    category="read",
    allowed_roles=["student", "faculty"],
    handler=community_tools.handle_event_club_registration_guidance,
)

SEARCH_FACULTY_COMMITTEES = Tool(
    name="search_faculty_committees",
    description=(
        "Search or list FACULTY / institutional governance committees (ToR domain: "
        "Academic Council, BTP, Exam, Research, Placement, ICC/POSH, etc.) by topic. "
        "Do NOT use for student hobby clubs or SBG student committees — use "
        "search_student_clubs instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic keyword; omit or empty to list governance committees broadly.",
            },
        },
    },
    category="read",
    allowed_roles=["faculty"],
    handler=community_tools.handle_search_faculty_committees,
)

FACULTY_COMMITTEE_RESPONSIBILITIES = Tool(
    name="faculty_committee_responsibilities",
    description=(
        "Get the Terms of Reference summary (mandate, composition, responsibilities) "
        "for a named FACULTY / institutional governance committee (e.g. BTP Committee, "
        "Academic Council, Exam Committee). Not for student clubs — use "
        "get_student_club_info / get_club_members for those."
    ),
    parameters={
        "type": "object",
        "properties": {"committee_name": {"type": "string"}},
        "required": ["committee_name"],
    },
    category="read",
    allowed_roles=["faculty"],
    handler=community_tools.handle_faculty_committee_responsibilities,
)

SCREEN_SCHOLARSHIP_ELIGIBILITY = Tool(
    name="screen_scholarship_eligibility",
    description=(
        "Cross-references the requester's own academic profile (branch, year, category, "
        "cgpa, annual_income) against university scholarship/financial-aid rules in the KB "
        "to check eligibility and return application requirements. Guidance only — no "
        "application is submitted. Prefer this over lookup_university_policy / "
        "lookup_admissions_info for personal scholarship eligibility."
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


# ── Domain KB retrieval skills (read-only, non-ERP) ─────────────────────────

LOOKUP_ACADEMIC_CALENDAR = Tool(
    name="lookup_academic_calendar",
    description=(
        "Look up academic calendar dates, semester deadlines, and holidays from "
        "published academics KB documents. Use for 'when is mid-sem' / 'academic calendar'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Date topic or semester; omit for overview."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_academic_calendar,
)

LOOKUP_COURSE_POLICY = Tool(
    name="lookup_course_policy",
    description=(
        "Look up a named course's published course policy (evaluation scheme, attendance, "
        "instructor if listed) from academics course-policy documents. Use when the user "
        "asks about a specific course code/title policy — not personal ERP grades."
    ),
    parameters={
        "type": "object",
        "properties": {"course": {"type": "string", "description": "Course code or title."}},
        "required": ["course"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_course_policy,
)

LOOKUP_ACADEMIC_REQUIREMENTS = Tool(
    name="lookup_academic_requirements",
    description=(
        "Look up degree/program academic requirements, credits, and curriculum rules from "
        "academics policy documents (BTech/MTech/MSc/PhD etc.)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "program": {"type": "string", "description": "Program name; omit for broad overview."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_academic_requirements,
)

LOOKUP_ADMISSIONS_INFO = Tool(
    name="lookup_admissions_info",
    description=(
        "Look up UG/PG/PhD/dual-degree admissions eligibility, process, seats, or fees "
        "from admissions KB documents. Not for personal scholarship screening — use "
        "screen_scholarship_eligibility for that."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Program or admissions topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_admissions_info,
)

LOOKUP_PUBLIC_TIMETABLE_DOCS = Tool(
    name="lookup_public_timetable_docs",
    description=(
        "Look up published campus TT/timetable PDFs, notices, or announcements about the "
        "timetable itself (e.g. 'where is the official timetable notice', 'when was the TT "
        "revised'). Do NOT use this for an actual class schedule by year/sem/branch/section — "
        "use get_cohort_timetable for that (it queries the live schedule directly and is far "
        "more reliable). Do NOT use for the user's personal editable timetable — use personal "
        "timetable tools (get_my_timetable etc.) for that."
    ),
    parameters={
        "type": "object",
        "properties": {
            "program": {"type": "string", "description": "Programme/section name for the public TT doc."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_public_timetable_docs,
)

LOOKUP_UNIVERSITY_POLICY = Tool(
    name="lookup_university_policy",
    description=(
        "Look up campus/institutional policies and administration guidelines (attendance, "
        "fees, grievance, anti-ragging, hostel allotment, IT, etc.) from policies / "
        "administration / internal_policies KB. Not for faculty ToR committees (use "
        "faculty_committee tools) or student clubs (use club tools)."
    ),
    parameters={
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_lookup_university_policy,
)

LOOKUP_FACULTY_PROFILE = Tool(
    name="lookup_faculty_profile",
    description=(
        "Look up a named faculty/staff member's published profile (designation, research "
        "areas, contact if listed) from faculty/people KB. Not for student club convenors "
        "— use lookup_club_office_bearers for those."
    ),
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_lookup_faculty_profile,
)

SEARCH_PEOPLE_DIRECTORY = Tool(
    name="search_people_directory",
    description=(
        "Search faculty/staff/people directories by department, role, or keyword. "
        "Do NOT use for student club member rosters — use get_club_members instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Department, role, or keyword."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_search_people_directory,
)

LOOKUP_RESEARCH_INFO = Tool(
    name="lookup_research_info",
    description=(
        "Look up research areas, labs, publications, IRB, and research policies from "
        "research KB. For personal faculty seed-grant / CPDA application checklists use "
        "seed_grant_guidance / cpda_travel_approval_guidance instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research area, lab, or policy topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=research_careers_kb_tools.handle_lookup_research_info,
)

LOOKUP_PLACEMENT_CAREERS_INFO = Tool(
    name="lookup_placement_careers_info",
    description=(
        "Look up placement process, policies, statistics, brochure facts, and careers "
        "information from placements/careers KB. Advisory only — does not register the "
        "student with the Placement Cell."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Placement/careers topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=research_careers_kb_tools.handle_lookup_placement_careers_info,
)

LOOKUP_CAMPUS_EVENTS_NOTICES = Tool(
    name="lookup_campus_events_notices",
    description=(
        "Look up campus events, announcements, notices, and news articles. For joining a "
        "student club (not a one-off event), prefer get_student_club_info / "
        "event_club_registration_guidance."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Event, announcement, or news topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_campus_events_notices,
)

LOOKUP_CAMPUS_FACILITIES = Tool(
    name="lookup_campus_facilities",
    description=(
        "Look up campus infrastructure/facilities (hostel halls, sports complex, resource "
        "centre, medical, food court, ICT, lecture complex, security, directions). For a "
        "specific hostel complaint to route, prefer hostel_complaint_guidance."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Facility or infrastructure topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_campus_facilities,
)

LOOKUP_STUDENT_SERVICES_INFO = Tool(
    name="lookup_student_services_info",
    description=(
        "Look up non-club student services (dean of students, medical SOP, holiday list, "
        "contacts, first-year guidance). For bonafide/transcript/ID use "
        "certificate_request_guidance; for club membership use club tools."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Student-services topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_student_services_info,
)

LOOKUP_ALUMNI_INFO = Tool(
    name="lookup_alumni_info",
    description=(
        "Look up alumni profiles, batches, or alumni services from alumni KB documents."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Alumni name, batch, or topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_alumni_info,
)

LOOKUP_ACHIEVEMENTS = Tool(
    name="lookup_achievements",
    description=(
        "Look up student/faculty awards and recognitions from achievements KB documents."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Award, competition, or achievement topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_achievements,
)

LOOKUP_CEP_INFO = Tool(
    name="lookup_cep_info",
    description=(
        "Look up Continuing Education Programme (CEP) courses and policy from cep KB. "
        "Advisory only — does not enrol anyone."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "CEP course or policy topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_cep_info,
)


# ── Domain KB retrieval skills (read-only, non-ERP) ─────────────────────────

LOOKUP_ACADEMIC_CALENDAR = Tool(
    name="lookup_academic_calendar",
    description=(
        "Look up academic calendar dates, semester deadlines, and holidays from "
        "published academics KB documents. Use for 'when is mid-sem' / 'academic calendar'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Date topic or semester; omit for overview."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_academic_calendar,
)

LOOKUP_COURSE_POLICY = Tool(
    name="lookup_course_policy",
    description=(
        "Look up a named course's published course policy (evaluation scheme, attendance, "
        "instructor if listed) from academics course-policy documents. Use when the user "
        "asks about a specific course code/title policy — not personal ERP grades."
    ),
    parameters={
        "type": "object",
        "properties": {"course": {"type": "string", "description": "Course code or title."}},
        "required": ["course"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_course_policy,
)

LOOKUP_ACADEMIC_REQUIREMENTS = Tool(
    name="lookup_academic_requirements",
    description=(
        "Look up degree/program academic requirements, credits, and curriculum rules from "
        "academics policy documents (BTech/MTech/MSc/PhD etc.)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "program": {"type": "string", "description": "Program name; omit for broad overview."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_academic_requirements,
)

LOOKUP_ADMISSIONS_INFO = Tool(
    name="lookup_admissions_info",
    description=(
        "Look up UG/PG/PhD/dual-degree admissions eligibility, process, seats, or fees "
        "from admissions KB documents. Not for personal scholarship screening — use "
        "screen_scholarship_eligibility for that."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Program or admissions topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_admissions_info,
)

LOOKUP_PUBLIC_TIMETABLE_DOCS = Tool(
    name="lookup_public_timetable_docs",
    description=(
        "Look up published campus TT/timetable PDFs, notices, or announcements about the "
        "timetable itself (e.g. 'where is the official timetable notice', 'when was the TT "
        "revised'). Do NOT use this for an actual class schedule by year/sem/branch/section — "
        "use get_cohort_timetable for that (it queries the live schedule directly and is far "
        "more reliable). Do NOT use for the user's personal editable timetable — use personal "
        "timetable tools (get_my_timetable etc.) for that."
    ),
    parameters={
        "type": "object",
        "properties": {
            "program": {"type": "string", "description": "Programme/section name for the public TT doc."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=academic_kb_tools.handle_lookup_public_timetable_docs,
)

LOOKUP_UNIVERSITY_POLICY = Tool(
    name="lookup_university_policy",
    description=(
        "Look up campus/institutional policies and administration guidelines (attendance, "
        "fees, grievance, anti-ragging, hostel allotment, IT, etc.) from policies / "
        "administration / internal_policies KB. Not for faculty ToR committees (use "
        "faculty_committee tools) or student clubs (use club tools)."
    ),
    parameters={
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_lookup_university_policy,
)

LOOKUP_FACULTY_PROFILE = Tool(
    name="lookup_faculty_profile",
    description=(
        "Look up a named faculty/staff member's published profile (designation, research "
        "areas, contact if listed) from faculty/people KB. Not for student club convenors "
        "— use lookup_club_office_bearers for those."
    ),
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_lookup_faculty_profile,
)

SEARCH_PEOPLE_DIRECTORY = Tool(
    name="search_people_directory",
    description=(
        "Search faculty/staff/people directories by department, role, or keyword. "
        "Do NOT use for student club member rosters — use get_club_members instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Department, role, or keyword."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=admin_people_kb_tools.handle_search_people_directory,
)

LOOKUP_RESEARCH_INFO = Tool(
    name="lookup_research_info",
    description=(
        "Look up research areas, labs, publications, IRB, and research policies from "
        "research KB. For personal faculty seed-grant / CPDA application checklists use "
        "seed_grant_guidance / cpda_travel_approval_guidance instead."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Research area, lab, or policy topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=research_careers_kb_tools.handle_lookup_research_info,
)

LOOKUP_PLACEMENT_CAREERS_INFO = Tool(
    name="lookup_placement_careers_info",
    description=(
        "Look up placement process, policies, statistics, brochure facts, and careers "
        "information from placements/careers KB. Advisory only — does not register the "
        "student with the Placement Cell."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Placement/careers topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=research_careers_kb_tools.handle_lookup_placement_careers_info,
)

LOOKUP_CAMPUS_EVENTS_NOTICES = Tool(
    name="lookup_campus_events_notices",
    description=(
        "Look up campus events, announcements, notices, and news articles. For joining a "
        "student club (not a one-off event), prefer get_student_club_info / "
        "event_club_registration_guidance."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Event, announcement, or news topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_campus_events_notices,
)

LOOKUP_CAMPUS_FACILITIES = Tool(
    name="lookup_campus_facilities",
    description=(
        "Look up campus infrastructure/facilities (hostel halls, sports complex, resource "
        "centre, medical, food court, ICT, lecture complex, security, directions). For a "
        "specific hostel complaint to route, prefer hostel_complaint_guidance."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Facility or infrastructure topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_campus_facilities,
)

LOOKUP_STUDENT_SERVICES_INFO = Tool(
    name="lookup_student_services_info",
    description=(
        "Look up non-club student services (dean of students, medical SOP, holiday list, "
        "contacts, first-year guidance). For bonafide/transcript/ID use "
        "certificate_request_guidance; for club membership use club tools."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Student-services topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_student_services_info,
)

LOOKUP_ALUMNI_INFO = Tool(
    name="lookup_alumni_info",
    description=(
        "Look up alumni profiles, batches, or alumni services from alumni KB documents."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Alumni name, batch, or topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_alumni_info,
)

LOOKUP_ACHIEVEMENTS = Tool(
    name="lookup_achievements",
    description=(
        "Look up student/faculty awards and recognitions from achievements KB documents."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Award, competition, or achievement topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_achievements,
)

LOOKUP_CEP_INFO = Tool(
    name="lookup_cep_info",
    description=(
        "Look up Continuing Education Programme (CEP) courses and policy from cep KB. "
        "Advisory only — does not enrol anyone."
    ),
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "CEP course or policy topic."},
        },
    },
    category="read",
    allowed_roles=["student", "faculty"],
    handler=campus_info_kb_tools.handle_lookup_cep_info,
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
        SEARCH_STUDENT_CLUBS, GET_STUDENT_CLUB_INFO,
        GET_CLUB_MEMBERS, LOOKUP_CLUB_OFFICE_BEARERS,
        EVENT_CLUB_REGISTRATION_GUIDANCE,
        SEARCH_FACULTY_COMMITTEES, FACULTY_COMMITTEE_RESPONSIBILITIES,
        SCREEN_SCHOLARSHIP_ELIGIBILITY, UPDATE_TRACKING_FLAGS,
        LOOKUP_ACADEMIC_CALENDAR, LOOKUP_COURSE_POLICY, LOOKUP_ACADEMIC_REQUIREMENTS,
        LOOKUP_ADMISSIONS_INFO, LOOKUP_PUBLIC_TIMETABLE_DOCS,
        LOOKUP_UNIVERSITY_POLICY, LOOKUP_FACULTY_PROFILE, SEARCH_PEOPLE_DIRECTORY,
        LOOKUP_RESEARCH_INFO, LOOKUP_PLACEMENT_CAREERS_INFO,
        LOOKUP_CAMPUS_EVENTS_NOTICES, LOOKUP_CAMPUS_FACILITIES,
        LOOKUP_STUDENT_SERVICES_INFO, LOOKUP_ALUMNI_INFO, LOOKUP_ACHIEVEMENTS,
        LOOKUP_CEP_INFO,
    ]
}

# KB-backed campus community tools (clubs / SBG / faculty ToR).
COMMUNITY_TOOL_NAMES: frozenset[str] = frozenset({
    "search_student_clubs",
    "get_student_club_info",
    "get_club_members",
    "lookup_club_office_bearers",
    "event_club_registration_guidance",
    "search_faculty_committees",
    "faculty_committee_responsibilities",
})

# Domain KB retrieval skills (academics, people, research, campus info).
KB_DOMAIN_TOOL_NAMES: frozenset[str] = frozenset({
    "lookup_academic_calendar",
    "lookup_course_policy",
    "lookup_academic_requirements",
    "lookup_admissions_info",
    "lookup_public_timetable_docs",
    "lookup_university_policy",
    "lookup_faculty_profile",
    "search_people_directory",
    "lookup_research_info",
    "lookup_placement_careers_info",
    "lookup_campus_events_notices",
    "lookup_campus_facilities",
    "lookup_student_services_info",
    "lookup_alumni_info",
    "lookup_achievements",
    "lookup_cep_info",
})

# Non-ERP tools exposed on the public-KB orchestrator path. Personal ERP
# tools stay gated behind PERSONAL / MIXED.
PUBLIC_KB_TOOL_NAMES: frozenset[str] = COMMUNITY_TOOL_NAMES | KB_DOMAIN_TOOL_NAMES


def tools_for_role(role: str) -> list[Tool]:
    return [t for t in TOOL_REGISTRY.values() if role in t.allowed_roles]


def community_tools_for_role(role: str) -> list[Tool]:
    return [
        t for t in TOOL_REGISTRY.values()
        if t.name in COMMUNITY_TOOL_NAMES and role in t.allowed_roles
    ]


def public_kb_tools_for_role(role: str) -> list[Tool]:
    return [
        t for t in TOOL_REGISTRY.values()
        if t.name in PUBLIC_KB_TOOL_NAMES and role in t.allowed_roles
    ]
