"""
Administration / policies / people directory KB skills — read-only.

KB sources (primary):
  policies / administration / internal_policies — campus & institutional rules
  faculty / people / student_faculty — directory & profiles (NOT club rosters)

Faculty governance ToR committees remain in community_tools
(search_faculty_committees / faculty_committee_responsibilities).
Student club rosters remain in community_tools (get_club_members etc.).
"""

from .kb_retrieval import (
    FACULTY_ROLES,
    PUBLIC_READER_ROLES,
    audit,
    identity_role,
    require_role,
    run_kb_query,
)

_POLICY_PROMPT = """
You are AURA's university policy assistant. Using ONLY the retrieved policy /
administration context, summarize the rule, procedure, or guideline asked about.
Rules:
- Use ONLY content from the retrieved text. Never invent clauses or contacts.
- Name the policy document when identifiable.
- If the query is about faculty governance ToR committees, say those belong to
  the faculty committee tools.
- If the query is about scholarships, mention screen_scholarship_eligibility
  for personal eligibility screening.
"""

_FACULTY_PROFILE_PROMPT = """
You are AURA's faculty directory assistant. Using ONLY the retrieved faculty
profile / people context for a named person, summarize:
1. Name and designation
2. Research / teaching areas (if stated)
3. Contact / office (only if present)
4. Other published profile facts
Never invent email, phone, or publications. This is public KB profile data,
not an ERP HR lookup. Do NOT treat student club convenors as faculty profiles
unless the context is clearly a faculty page.
"""

_PEOPLE_SEARCH_PROMPT = """
You are AURA's people-directory assistant. Using ONLY the retrieved faculty /
staff / people lists, list matching people with designation when available.
Rules:
- Prefer faculty profiles, staff lists, doctoral scholars, boards of studies.
- Do NOT dump student club rosters — those belong to get_club_members /
  lookup_club_office_bearers.
- Never invent people absent from the retrieved text.
"""


def handle_lookup_university_policy(identity, topic: str, request_context=None, **kwargs) -> dict:
    """Campus/institutional policies from policies, administration, internal_policies."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up university policies.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("policy") or "").strip()
    if not topic:
        return {"response": "Please provide a policy topic or name.", "sources": []}

    role = identity_role(identity)
    # Faculty-authored / internal docs need faculty retrieval authorization.
    retrieval_role = "faculty_general" if role in FACULTY_ROLES else "student"
    query = (
        f"{topic} university policy administration guidelines rules SOP "
        f"grievance hostel attendance fee structure internal policy"
    )
    out = run_kb_query(
        query, retrieval_role, _POLICY_PROMPT, f"University policy topic: {topic}",
        request_context=request_context,
        empty_response=(
            "I couldn't find that policy in the knowledge base. Try the exact "
            "policy name (e.g. attendance policy, hostel allotment, anti-ragging)."
        ),
    )
    audit(identity, "lookup_university_policy", topic)
    return out


def handle_lookup_faculty_profile(identity, name: str, request_context=None, **kwargs) -> dict:
    """Named faculty/staff profile from data/faculty/ and related people docs."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up faculty profiles.",
    )
    name = (name or kwargs.get("faculty_name") or "").strip()
    if not name:
        return {"response": "Please provide a faculty or staff member's name.", "sources": []}
    query = (
        f"{name} faculty profile designation research areas teaching contact "
        f"email office professor associate assistant"
    )
    out = run_kb_query(
        query, "student", _FACULTY_PROFILE_PROMPT, f"Faculty / people profile: {name}",
        request_context=request_context,
        empty_response=(
            f"I couldn't find a published profile for '{name}'. "
            "Try the full name as listed on the faculty directory."
        ),
    )
    audit(identity, "lookup_faculty_profile", name)
    return out


def handle_search_people_directory(identity, query: str = "", request_context=None, **kwargs) -> dict:
    """Search faculty/staff/people directories (non-club)."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty searching the people directory.",
    )
    topic = (query or kwargs.get("topic") or kwargs.get("department") or "").strip()
    if topic:
        retrieval_query = (
            f"{topic} faculty staff directory list professor designation "
            f"department doctoral scholars teaching fellows"
        )
        user_message = f"Find people related to: {topic}"
    else:
        retrieval_query = (
            "faculty directory staff list teaching fellows professors "
            "department directory overview"
        )
        user_message = "Summarize available faculty/staff directory coverage."
    out = run_kb_query(
        retrieval_query, "student", _PEOPLE_SEARCH_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching people in the directory knowledge base.",
    )
    audit(identity, "search_people_directory", topic or "overview")
    return out
