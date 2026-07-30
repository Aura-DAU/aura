"""
Community/governance advisory tools — read-only, KB-retrieval-driven.

event_club_registration_guidance: given a club/event name, returns the
membership/registration process and the convenor's contact.

faculty_committee_responsibilities: given a committee name, retrieves its
Terms of Reference from the governance/ KB and returns a structured
responsibility list.
"""

import os
from dotenv import load_dotenv
from pipeline.key_manager import KeyManager
from ..personal_data.audit import audit_log

load_dotenv()

_retrieval = None


def _get_retrieval_pipeline():
    global _retrieval
    if _retrieval is None:
        from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
        _retrieval = RetrievalPipeline()
    return _retrieval

_EVENT_SYSTEM_PROMPT = """
You are AURA's campus life assistant. Using ONLY the retrieved context about
a club or event, explain:
1. How to join / register
2. Any eligibility or membership criteria mentioned
3. The convenor / point-of-contact, if named in the retrieved text
If the retrieved context doesn't name a specific contact or process, say so
rather than inventing one. AURA cannot register the student — end with a
reminder to complete registration through the club/event's own channel.
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
"""


def _run(query: str, user_role: str, system_prompt: str, user_message: str) -> dict:
    result = _get_retrieval_pipeline().get_context(query, user_role=user_role)
    context = result.get("context", "")
    sources = result.get("sources", [])

    if not context.strip():
        return {
            "response": "I couldn't find that in the knowledge base — try the exact club, event, or committee name.",
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


# ── event_club_registration_guidance ────────────────────────────────────────
def handle_event_club_registration_guidance(identity, name: str, **kwargs) -> dict:
    """name = club or event name. Read-only advisory, no registration write."""
    query = f"{name} club event membership registration process convenor contact"
    out = _run(query, "student", _EVENT_SYSTEM_PROMPT, f"Club/event: {name}")
    audit_log(identity, query="event_club_registration_guidance", allowed=True,
              target=name)
    return out


# ── faculty_committee_responsibilities ──────────────────────────────────────
def handle_faculty_committee_responsibilities(identity, committee_name: str, **kwargs) -> dict:
    """committee_name e.g. 'Academic Council', 'BTP Committee', 'POSH Committee'."""
    if not identity or identity.get("role") not in (
        "faculty", "faculty_general", "faculty_coord",
        "faculty_convenor_ug", "faculty_convenor_pg",
        "dean_faculty", "dean_academic", "superadmin",
    ):
        raise PermissionError("This tool is for faculty members.")
    query = f"{committee_name} terms of reference composition responsibilities"
    out = _run(query, "faculty_general", _TOR_SYSTEM_PROMPT, f"Committee: {committee_name}")
    audit_log(identity, query="faculty_committee_responsibilities", allowed=True,
              target=committee_name)
    return out
