"""
Community/governance advisory tools — read-only, KB-retrieval-driven.

Student-club tools (SBG hobby clubs & student committees — NOT faculty ToR):
  search_student_clubs: list/search clubs matching an interest or keyword.
  get_student_club_info: purpose, membership criteria, convenor/contact, how to join.
  get_club_members: published roster (members + roles) for a named club/committee.
  lookup_club_office_bearers: convenor / dy. convenor / faculty mentor / club email.
  event_club_registration_guidance: registration/membership process for a
    named club or campus event.

Faculty-governance tools (institutional ToR committees — NOT student clubs):
  search_faculty_committees: list/search governance committees by topic.
  faculty_committee_responsibilities: ToR summary for a named committee.

KB sources (primary):
  student clubs/SBG / rosters — data/student_faculty/ (Club Committee Data,
    C_DCs Information, Core Members lists), data/policies/student_clubs_*,
    data/student_services/committees/, data/events/
  faculty ToR — data/governance/, data/academics/*committees*

Member/roster tools use ONLY campus-published KB documents (authorization
student/faculty). They never query ERP personal records — there is no ERP
club-membership connector, and private student data must not be invented.
"""

import os
from datetime import date
from dotenv import load_dotenv
from pipeline.key_manager import KeyManager
from ..personal_data.audit import audit_log


def _identity_payload(identity):
    if identity is None:
        return {}
    if isinstance(identity, dict):
        return identity
    return getattr(identity, "as_dict", lambda: {})()


def _identity_role(identity) -> str | None:
    payload = _identity_payload(identity)
    if not payload:
        return None
    return payload.get("role")


load_dotenv()

_retrieval = None

_STUDENT_ROLES = ("student", "guest")
_FACULTY_ROLES = (
    "faculty", "faculty_general", "faculty_coord",
    "faculty_convenor_ug", "faculty_convenor_pg",
    "dean_faculty", "dean_academic", "superadmin",
)
# Club discovery is useful to faculty mentors as well as students.
_CLUB_READER_ROLES = _STUDENT_ROLES + _FACULTY_ROLES


def _current_academic_year(today: date | None = None) -> str:
    current = today or date.today()
    start = current.year if current.month >= 7 else current.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def _get_retrieval_pipeline():
    global _retrieval
    if _retrieval is None:
        from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
        _retrieval = RetrievalPipeline()
    return _retrieval


_EVENT_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved context about
a student club or campus event, explain:
1. How to join / register
2. Any eligibility or membership criteria mentioned
3. The convenor / point-of-contact / club email, if named in the retrieved text
If the retrieved context doesn't name a specific contact or process, say so
rather than inventing one. AURA cannot register the student — end with a
reminder to complete registration through the club/event's own channel.

This tool is for STUDENT clubs / SBG student committees / campus events —
not faculty governance Terms of Reference committees.
"""

_CLUB_INFO_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved context about
a named STUDENT club or SBG student committee (hobby club, Cultural/Sports/
Hostel Management committee, IEEE SB, etc.), produce a structured summary:
1. Purpose / what the club or student committee does
2. Membership — who can join, any criteria mentioned
3. Convenor / Dy. Convenor / faculty mentor / contact email (only if named)
4. How to join or get involved
If a section is missing from the retrieved text, say "Not specified in the
retrieved documents" for that section — never invent contacts or processes.
AURA cannot enrol anyone — remind the student to contact the club/SBG channel.

Do NOT treat faculty governance ToR bodies (Academic Council, BTP Committee,
Exam Committee, etc.) as student clubs; if the context is clearly a faculty
ToR document, say this looks like a faculty committee and suggest the
faculty committee tools instead.
"""

_CLUB_MEMBERS_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved SBG / club
roster context for a named STUDENT club or SBG student committee, list the
people associated with it.

Structure the answer as:
1. Office-bearers (Convenor, Dy. Convenor / Deputy, Faculty Mentor) — if present
2. Other published members / core members — if present
3. Roster academic year / document title, if identifiable in the context

Rules:
- Include name, position/role, and student ID / contact / email ONLY when
  those fields appear in the retrieved text. Never invent members or contacts.
- Prefer the most recent roster year when multiple years appear; mention the
  year you used.
- This is campus-published club roster data, not a private ERP lookup. If the
  retrieved context has no roster for that club, say so clearly.
- Do NOT treat faculty governance ToR committees as student club rosters.
"""

_OFFICE_BEARERS_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved context for a
named STUDENT club or SBG student committee, identify the current
office-bearers / points of contact:
- Convenor (and student ID if stated)
- Dy. Convenor / Deputy Convenor (and student ID if stated)
- Faculty Mentor (if stated)
- Club / committee email (if stated)

Rules:
- Use ONLY names and contacts present in the retrieved text. Never invent.
- Prefer C_DCs / convenor sheets with the highest academic year (e.g. 2026-27
  over 2025-26 over 24-25). Never treat scraped_date as the roster year.
- If older and newer rosters both appear, answer from the newest and name the year.
- If office-bearers are not in the retrieved context, say so — do not guess
  from unrelated clubs.
- This is published SBG roster data, not an ERP personal-data lookup.
"""

_SEARCH_CLUBS_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved context,
list student clubs and SBG student committees that match the user's interest
or keyword.

For each match, give:
- Name
- One-line purpose (if available)
- Convenor or contact email (only if named in the context)

Rules:
- Prefer STUDENT clubs / SBG committees / hobby clubs from SBG club lists.
- Do NOT list faculty governance ToR committees (Academic Council, BTP,
  Research Committee ToR, etc.) as if they were joinable student clubs.
- If nothing relevant appears in the context, say so and suggest trying a
  different keyword (e.g. music, coding, cultural, sports).
- Do not invent clubs that are not in the retrieved text.
"""

_TOR_SYSTEM_PROMPT = """
You are AURA's faculty governance assistant. Using ONLY the retrieved
committee Terms of Reference (ToR) context, produce a structured summary:
1. Committee purpose/mandate
2. Composition (who sits on it, if stated)
3. Key responsibilities
4. Meeting frequency / reporting line, if stated
If the retrieved context doesn't cover a section, say "Not specified in the
retrieved ToR document" for that section rather than guessing.

This tool is for FACULTY / institutional governance committees (ToR docs
under governance/academics) — not student hobby clubs or SBG student
committees. If the context is clearly a student club roster, say so.
"""

_SEARCH_COMMITTEES_SYSTEM_PROMPT = """
You are AURA's faculty governance assistant. Using ONLY the retrieved
context, list institutional / faculty governance committees that match
the user's topic or keyword (e.g. research, examinations, BTP, POSH,
placements, academic policy).

For each match, give:
- Committee name
- One-line mandate / purpose (if available)
- Note if a ToR document is referenced

Rules:
- Prefer governance ToR and academic-policy committee documents.
- Do NOT list student hobby clubs (Music Club, Programming Club, etc.) as
  faculty committees — those belong to the student-club tools.
- Student-facing statutory bodies (Anti-Ragging, Internal Complaints /
  POSH, Grievance Redressal) may be included when relevant.
- Do not invent committees absent from the retrieved text.
"""


def _run(
    query: str,
    user_role: str,
    system_prompt: str,
    user_message: str,
    request_context=None,
    empty_response: str | None = None,
) -> dict:
    academic_scope = getattr(request_context, "academic_scope", None) if request_context else None
    pipeline = _get_retrieval_pipeline()
    try:
        result = pipeline.get_context(
            query,
            user_role=user_role,
            academic_scope=academic_scope,
        )
    except TypeError:
        result = pipeline.get_context(query, user_role=user_role)
    context = result.get("context", "")
    sources = result.get("sources", [])

    if not context.strip():
        if result.get("abstention_reason") == "academic_scope_unavailable":
            from pipeline.aura_chat import ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE
            return {"response": ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE, "sources": []}
        return {
            "response": empty_response or (
                "I couldn't find that in the knowledge base — try the exact "
                "club, event, or committee name."
            ),
            "sources": [],
        }

    def _execute(client):
        return client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": f"{user_message}\n\nRetrieved context:\n{context}"},
            ],
        )

    response = KeyManager.call_with_rotation(_execute, max_retries=3)
    text = (
        response.choices[0].message.content
        if response
        else "Unable to generate guidance right now — please try again."
    )
    return {"response": text, "sources": sources}


def _require_role(identity, allowed: tuple[str, ...], message: str) -> None:
    role = _identity_role(identity)
    if role not in allowed:
        raise PermissionError(message)


# ── search_student_clubs ────────────────────────────────────────────────────
def handle_search_student_clubs(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """List/search student clubs & SBG student committees by interest/keyword."""
    _require_role(
        identity, _CLUB_READER_ROLES,
        "This tool is for students (and faculty mentors) browsing student clubs.",
    )
    topic = (topic or kwargs.get("query") or "").strip()
    if topic:
        query = (
            f"{topic} student club SBG hobby club committee list convenor "
            f"faculty mentor contact email Club Committee C_DCs"
        )
        user_message = f"Find student clubs / SBG committees related to: {topic}"
    else:
        query = (
            "list of student clubs SBG hobby clubs committees convenor "
            "faculty mentor Club Committee C_DCs information student clubs policy"
        )
        user_message = "List available student clubs and SBG student committees."
    out = _run(
        query, "student", _SEARCH_CLUBS_SYSTEM_PROMPT, user_message,
        request_context=request_context,
        empty_response=(
            "I couldn't find matching student clubs in the knowledge base. "
            "Try a keyword like music, coding, cultural, sports, or research."
        ),
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="search_student_clubs", allowed=True, target=topic or "all")
    return out


# ── get_student_club_info ───────────────────────────────────────────────────
def handle_get_student_club_info(identity, club_name: str, request_context=None, **kwargs) -> dict:
    """Purpose, membership, convenor/contact, how to join for a named student club."""
    _require_role(
        identity, _CLUB_READER_ROLES,
        "This tool is for students (and faculty mentors) looking up student clubs.",
    )
    club_name = (club_name or "").strip()
    if not club_name:
        return {
            "response": "Please provide a student club or SBG committee name.",
            "sources": [],
        }
    query = (
        f"{club_name} student club SBG committee purpose membership convenor "
        f"dy convenor faculty mentor contact email how to join Club Committee C_DCs"
    )
    out = _run(
        query, "student", _CLUB_INFO_SYSTEM_PROMPT, f"Student club / SBG committee: {club_name}",
        request_context=request_context,
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="get_student_club_info", allowed=True, target=club_name)
    return out


# ── get_club_members ────────────────────────────────────────────────────────
def handle_get_club_members(identity, club_name: str, request_context=None, **kwargs) -> dict:
    """Published KB roster for a named student club / SBG committee. No ERP."""
    _require_role(
        identity, _CLUB_READER_ROLES,
        "This tool is for students (and faculty mentors) looking up published club rosters.",
    )
    club_name = (club_name or "").strip()
    if not club_name:
        return {
            "response": "Please provide a student club or SBG committee name.",
            "sources": [],
        }
    query = (
        f"{club_name} club committee core members list roster convenor "
        f"dy convenor member student ID position C_DCs Information "
        f"Core Members office bearers"
    )
    out = _run(
        query, "student", _CLUB_MEMBERS_SYSTEM_PROMPT,
        f"Published roster for student club / SBG committee: {club_name}",
        request_context=request_context,
        empty_response=(
            "I couldn't find a published member roster for that club in the "
            "knowledge base. Try the exact club/committee name from the SBG list."
        ),
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="get_club_members", allowed=True, target=club_name)
    return out


# ── lookup_club_office_bearers ──────────────────────────────────────────────
def handle_lookup_club_office_bearers(identity, club_name: str, request_context=None, **kwargs) -> dict:
    """Convenor / dy. convenor / mentor / email from published SBG C_DCs sheets."""
    _require_role(
        identity, _CLUB_READER_ROLES,
        "This tool is for students (and faculty mentors) looking up club office-bearers.",
    )
    club_name = (club_name or "").strip()
    if not club_name:
        return {
            "response": "Please provide a student club or SBG committee name.",
            "sources": [],
        }
    academic_year = _current_academic_year()
    query = (
        f"{club_name} club committee convenor dy convenor deputy faculty mentor "
        f"email contact C_DCs Information office bearers "
        f"Convener Name Dy. Convener Name current latest academic year {academic_year}"
    )
    out = _run(
        query, "student", _OFFICE_BEARERS_SYSTEM_PROMPT,
        f"Office-bearers / contacts for student club / SBG committee: {club_name}. "
        f"Use the {academic_year} roster; use an older roster only if no "
        "current-year record exists, and state that limitation.",
        request_context=request_context,
        empty_response=(
            "I couldn't find published office-bearer contacts for that club. "
            "Try the exact name (e.g. Programming Club, Cultural Committee)."
        ),
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="lookup_club_office_bearers", allowed=True, target=club_name)
    return out


# ── event_club_registration_guidance ────────────────────────────────────────
def handle_event_club_registration_guidance(identity, name: str, request_context=None, **kwargs) -> dict:
    """name = club or event name. Read-only advisory, no registration write."""
    _require_role(
        identity, _CLUB_READER_ROLES,
        "This tool is for students (and faculty mentors) asking about club/event registration.",
    )
    name = (name or "").strip()
    if not name:
        return {
            "response": "Please provide a club or event name.",
            "sources": [],
        }
    query = (
        f"{name} student club event SBG membership registration how to join "
        f"process convenor contact email faculty mentor"
    )
    out = _run(
        query, "student", _EVENT_SYSTEM_PROMPT, f"Club/event: {name}",
        request_context=request_context,
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="event_club_registration_guidance", allowed=True, target=name)
    return out


# ── search_faculty_committees ───────────────────────────────────────────────
def handle_search_faculty_committees(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """List/search faculty governance committees by topic (ToR domain)."""
    _require_role(identity, _FACULTY_ROLES, "This tool is for faculty members.")
    topic = (topic or kwargs.get("query") or "").strip()
    if topic:
        query = (
            f"{topic} faculty committee terms of reference ToR mandate "
            f"composition governance academic policy"
        )
        user_message = f"Find faculty / governance committees related to: {topic}"
    else:
        query = (
            "list faculty governance committees terms of reference ToR "
            "Academic Council BTP Exam Research Placement Internal Complaints"
        )
        user_message = "List institutional / faculty governance committees with ToR coverage."
    out = _run(
        query, "faculty_general", _SEARCH_COMMITTEES_SYSTEM_PROMPT, user_message,
        request_context=request_context,
        empty_response=(
            "I couldn't find matching governance committees in the knowledge base. "
            "Try a keyword like BTP, examinations, research, placements, or POSH."
        ),
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="search_faculty_committees", allowed=True, target=topic or "all")
    return out


# ── faculty_committee_responsibilities ──────────────────────────────────────
def handle_faculty_committee_responsibilities(identity, committee_name: str, request_context=None, **kwargs) -> dict:
    """committee_name e.g. 'Academic Council', 'BTP Committee', 'POSH Committee'."""
    _require_role(identity, _FACULTY_ROLES, "This tool is for faculty members.")
    committee_name = (committee_name or "").strip()
    if not committee_name:
        return {
            "response": "Please provide a faculty / governance committee name.",
            "sources": [],
        }
    query = (
        f"{committee_name} committee terms of reference ToR mandate composition "
        f"responsibilities governance academic policy coordinator"
    )
    out = _run(
        query, "faculty_general", _TOR_SYSTEM_PROMPT, f"Committee: {committee_name}",
        request_context=request_context,
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="faculty_committee_responsibilities", allowed=True, target=committee_name)
    return out
