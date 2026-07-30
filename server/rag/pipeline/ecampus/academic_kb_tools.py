"""
Academics / admissions / public timetable KB skills — read-only.

KB sources (primary):
  academics — academic calendar, course policies, degree requirements,
              exam/registration rules under data/academics/
  admissions — data/admissions/ (UG/PG/PhD/dual-degree)
  public timetable docs — data/academics/timetable/ and data/time_table/
    (published lecture TT docs only — NOT personal ERP timetable tools)

Does NOT replace certificate_request_guidance or screen_scholarship_eligibility.
"""

from .kb_retrieval import (
    PUBLIC_READER_ROLES,
    audit,
    require_role,
    run_kb_query,
)

_CALENDAR_PROMPT = """
You are AURA's academic calendar assistant. Using ONLY the retrieved context,
summarize dates, deadlines, and calendar items the user asked about.
Rules:
- Use ONLY dates and events present in the retrieved text. Never invent dates.
- Prefer the most recent academic year when multiple years appear; name the year.
- If a date is missing, say "Not specified in the retrieved documents".
"""

_COURSE_POLICY_PROMPT = """
You are AURA's course-policy assistant. Using ONLY the retrieved course policy
context for a named course, summarize:
1. Course code / title
2. Instructor (if named)
3. Evaluation / grading scheme
4. Attendance / other key rules
5. Semester / academic year of the policy document
Never invent instructors, weights, or rules absent from the text.
If the wrong course appears, say so.
"""

_REQUIREMENTS_PROMPT = """
You are AURA's academic-requirements assistant. Using ONLY the retrieved
degree/program requirements context, summarize credit/course requirements,
eligibility, and key academic rules for the named program.
Never invent credit totals or course lists. Prefer the matching regulation year
when stated. Mark missing sections as "Not specified in the retrieved documents".
"""

_ADMISSIONS_PROMPT = """
You are AURA's admissions assistant. Using ONLY the retrieved admissions
context, explain eligibility, entrance tests, seats, fees, or process details
asked about. Never invent cutoffs, fees, or deadlines. Reminder: AURA cannot
submit applications — direct the user to the official admissions portal/office
when action is needed.
"""

_PUBLIC_TT_PROMPT = """
You are AURA's public timetable document assistant. Using ONLY retrieved
published lecture-timetable / programme TT documents (not personal ERP
schedules), summarize the requested programme/section schedule info.
Rules:
- This is public KB timetable documentation, NOT the user's personal timetable.
- For "my timetable" / personal edits, tell the user to use the personal
  timetable tools instead.
- Never invent slots, rooms, or courses absent from the text.
"""


def handle_lookup_academic_calendar(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Academic calendar dates/deadlines from data/academics/academic_calendar*."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up the academic calendar.",
    )
    topic = (topic or kwargs.get("query") or "").strip()
    if topic:
        query = f"{topic} academic calendar dates deadlines semester DAU DA-IICT"
        user_message = f"Academic calendar topic: {topic}"
    else:
        query = "academic calendar current semester important dates deadlines holidays"
        user_message = "Summarize key upcoming academic calendar dates."
    out = run_kb_query(
        query, "student", _CALENDAR_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find academic calendar details in the knowledge base.",
    )
    audit(identity, "lookup_academic_calendar", topic or "overview")
    return out


def handle_lookup_course_policy(identity, course: str, request_context=None, **kwargs) -> dict:
    """Course policy / syllabus-style rules for a named course code or title."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up course policies.",
    )
    course = (course or kwargs.get("course_code") or kwargs.get("course_name") or "").strip()
    if not course:
        return {"response": "Please provide a course code or course name.", "sources": []}
    query = (
        f"{course} course policy evaluation grading attendance instructor "
        f"syllabus autumn winter semester"
    )
    out = run_kb_query(
        query, "student", _COURSE_POLICY_PROMPT, f"Course policy for: {course}",
        request_context=request_context,
        empty_response=(
            f"I couldn't find a course policy document for '{course}'. "
            "Try the exact course code (e.g. IT623)."
        ),
    )
    audit(identity, "lookup_course_policy", course)
    return out


def handle_lookup_academic_requirements(identity, program: str = "", request_context=None, **kwargs) -> dict:
    """Degree/program academic requirements from data/academics/academic_policy_*."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up program requirements.",
    )
    program = (program or kwargs.get("programme") or kwargs.get("query") or "").strip()
    if program:
        query = (
            f"{program} academic requirements credits curriculum graduation "
            f"eligibility academic policy handbook"
        )
        user_message = f"Academic requirements for program: {program}"
    else:
        query = "academic requirements programs of study credit curriculum handbook overview"
        user_message = "Summarize available program academic-requirements documents."
    out = run_kb_query(
        query, "student", _REQUIREMENTS_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find academic requirements for that program in the knowledge base.",
    )
    audit(identity, "lookup_academic_requirements", program or "overview")
    return out


def handle_lookup_admissions_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Admissions eligibility/process from data/admissions/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up admissions information.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("program") or "").strip()
    if topic:
        query = (
            f"{topic} admissions eligibility entrance exam seats fees application "
            f"UG PG PhD dual degree how to apply"
        )
        user_message = f"Admissions question: {topic}"
    else:
        query = "admissions overview UG PG PhD programs eligibility how to apply"
        user_message = "Summarize admissions pathways covered in the knowledge base."
    out = run_kb_query(
        query, "student", _ADMISSIONS_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching admissions information in the knowledge base.",
    )
    audit(identity, "lookup_admissions_info", topic or "overview")
    return out


def handle_lookup_public_timetable_docs(identity, program: str = "", request_context=None, **kwargs) -> dict:
    """Published lecture TT docs only — not personal ERP / editable timetable."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up published timetable documents.",
    )
    program = (program or kwargs.get("query") or kwargs.get("section") or "").strip()
    if program:
        query = (
            f"{program} lecture timetable schedule section room slot "
            f"Autumn Winter published timetable programme"
        )
        user_message = (
            f"Public timetable document for: {program}. "
            "If this looks like a personal timetable request, say so."
        )
    else:
        query = "lecture timetable published programme section schedule Autumn Winter"
        user_message = "List available published public timetable documents."
    out = run_kb_query(
        query, "student", _PUBLIC_TT_PROMPT, user_message,
        request_context=request_context,
        empty_response=(
            "I couldn't find a published public timetable document for that. "
            "For your personal timetable, use the personal timetable tools."
        ),
    )
    audit(identity, "lookup_public_timetable_docs", program or "overview")
    return out
