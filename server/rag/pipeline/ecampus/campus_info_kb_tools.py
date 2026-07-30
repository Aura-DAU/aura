"""
Campus life & services KB skills — read-only (non-club).

KB sources (primary):
  events / announcements / notices / news_articles — campus news & events
  infrastructure — facilities (hostel halls, sports, RC, medical, food court)
  student_services — non-club student services (NOT club rosters)
  alumni — alumni profiles / connect docs
  achievements — awards & recognitions
  cep — Continuing Education Programme

Club/SBG membership & rosters remain in community_tools.
Certificate / hostel-complaint workflows remain in student_workflow_tools.
"""

from .kb_retrieval import (
    PUBLIC_READER_ROLES,
    audit,
    require_role,
    run_kb_query,
)

_EVENTS_PROMPT = """
You are AURA's campus events / announcements assistant. Using ONLY the
retrieved events, announcements, notices, or news context, summarize what
happened / is scheduled and any contacts mentioned.
Rules:
- Never invent event dates, venues, or organizers.
- Prefer the most recent matching item when years differ; name the year.
- For joining a STUDENT club (not a one-off event), suggest
  event_club_registration_guidance / get_student_club_info instead.
"""

_FACILITIES_PROMPT = """
You are AURA's campus facilities assistant. Using ONLY the retrieved
infrastructure context (halls of residence, sports complex, resource centre,
medical facility, food court, ICT, lecture complex, security, directions),
answer the facilities question.
Never invent timings, contacts, or amenities absent from the text.
"""

_STUDENT_SERVICES_PROMPT = """
You are AURA's student-services assistant. Using ONLY the retrieved
student-services context (dean of students, medical SOP, holiday list,
rules, contact pages — NOT club rosters), answer the question.
Rules:
- For bonafide/transcript/ID card process use certificate_request_guidance.
- For hostel complaint routing use hostel_complaint_guidance.
- For student club membership use the club tools.
- Never invent office contacts or procedures.
"""

_ALUMNI_PROMPT = """
You are AURA's alumni information assistant. Using ONLY the retrieved alumni
context, summarize alumni profiles, batches, or alumni services asked about.
Never invent employment details or contacts absent from the text.
"""

_ACHIEVEMENTS_PROMPT = """
You are AURA's achievements assistant. Using ONLY the retrieved awards /
achievements context, summarize the recognition asked about.
Never invent awards, winners, or years absent from the text.
"""

_CEP_PROMPT = """
You are AURA's Continuing Education Programme (CEP) assistant. Using ONLY
the retrieved CEP policy / course context, summarize eligibility, offerings,
or process details. Never invent fees or course lists. AURA cannot enrol
anyone — direct action to the official CEP channel when needed.
"""


def handle_lookup_campus_events_notices(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Events, announcements, notices, news from those data/ folders."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up campus events/notices.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("event") or "").strip()
    if topic:
        query = (
            f"{topic} campus event announcement notice news newsletter "
            f"workshop seminar festival"
        )
        user_message = f"Campus events / notices about: {topic}"
    else:
        query = "campus events announcements notices recent news newsletter overview"
        user_message = "Summarize recent campus events / notices in the knowledge base."
    out = run_kb_query(
        query, "student", _EVENTS_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching events or notices in the knowledge base.",
    )
    audit(identity, "lookup_campus_events_notices", topic or "overview")
    return out


def handle_lookup_campus_facilities(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Infrastructure / campus facilities from data/infrastructure/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up campus facilities.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("facility") or "").strip()
    if topic:
        query = (
            f"{topic} campus facility infrastructure halls of residence sports "
            f"complex resource centre medical food court lecture ICT security"
        )
        user_message = f"Campus facilities question: {topic}"
    else:
        query = (
            "campus infrastructure facilities halls of residence sports "
            "resource centre medical food court overview"
        )
        user_message = "Summarize campus facilities covered in the knowledge base."
    out = run_kb_query(
        query, "student", _FACILITIES_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching campus facilities information.",
    )
    audit(identity, "lookup_campus_facilities", topic or "overview")
    return out


def handle_lookup_student_services_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Non-club student services from data/student_services/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up student services.",
    )
    topic = (topic or kwargs.get("query") or "").strip()
    if topic:
        query = (
            f"{topic} student services dean of students medical holiday list "
            f"rules contact parents first year campus"
        )
        user_message = f"Student services question: {topic}"
    else:
        query = "student services dean of students contacts rules medical overview"
        user_message = "Summarize student-services information available."
    out = run_kb_query(
        query, "student", _STUDENT_SERVICES_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching student-services information.",
    )
    audit(identity, "lookup_student_services_info", topic or "overview")
    return out


def handle_lookup_alumni_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Alumni profiles / services from data/alumni/ and student_services/alumni."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up alumni information.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("name") or "").strip()
    if topic:
        query = f"{topic} alumni batch profile connect DAU DA-IICT"
        user_message = f"Alumni information about: {topic}"
    else:
        query = "alumni overview batches connect notable alumni DAU DA-IICT"
        user_message = "Summarize alumni information coverage in the knowledge base."
    out = run_kb_query(
        query, "student", _ALUMNI_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching alumni information in the knowledge base.",
    )
    audit(identity, "lookup_alumni_info", topic or "overview")
    return out


def handle_lookup_achievements(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Awards and recognitions from data/achievements/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up achievements.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("award") or "").strip()
    if topic:
        query = f"{topic} achievement award recognition prize competition student faculty"
        user_message = f"Achievements / awards about: {topic}"
    else:
        query = "achievements awards recognitions student faculty overview DAU"
        user_message = "Summarize notable achievements covered in the knowledge base."
    out = run_kb_query(
        query, "student", _ACHIEVEMENTS_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching achievements in the knowledge base.",
    )
    audit(identity, "lookup_achievements", topic or "overview")
    return out


def handle_lookup_cep_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Continuing Education Programme from data/cep/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up CEP information.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("course") or "").strip()
    if topic:
        query = f"{topic} CEP continuing education programme course AIP policy"
        user_message = f"CEP question: {topic}"
    else:
        query = "CEP continuing education programme courses policy overview AIP"
        user_message = "Summarize CEP offerings / policy in the knowledge base."
    out = run_kb_query(
        query, "student", _CEP_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching CEP information in the knowledge base.",
    )
    audit(identity, "lookup_cep_info", topic or "overview")
    return out
