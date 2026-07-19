"""
Faculty workflow tools — advisory-only guidance generated from KB policy text.

Per v7 policy directive #1 (read-only data access), these tools never write
to any external system (no ERP POST/PUT, no HR system integration). Each
tool:
  1. Retrieves the relevant policy document(s) via RetrievalPipeline
     (never hardcodes figures, deadlines, or eligibility rules in Python).
  2. Asks the LLM to compress that retrieved text into a structured
     checklist (eligibility → required documents → approval routing →
     deadlines), citing the source document.
  3. Returns plain data — the calling chat pipeline is responsible for
     rendering/streaming it, exactly like any other tool result.

If retrieval comes back empty, the tool says so explicitly rather than
guessing at policy details — same fail-safe posture as answer_generator.py.
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

_FACULTY_ROLES = (
    "faculty", "faculty_general", "faculty_coord",
    "faculty_convenor_ug", "faculty_convenor_pg",
    "dean_faculty", "dean_academic", "superadmin",
)

_STRUCTURING_SYSTEM_PROMPT = """
You are AURA's faculty workflow assistant. You turn retrieved DAU policy
text into a short, structured, advisory checklist for a faculty member.

Rules:
- Use ONLY the retrieved context below. Never invent amounts, deadlines,
  approval authorities, or eligibility rules that aren't in the text.
- If the retrieved context does not cover something, say "Not specified in
  the retrieved policy documents" for that field rather than guessing.
- This is advisory guidance only — AURA cannot submit, approve, or track
  any application on the faculty member's behalf. End every response with
  a one-line reminder to file the actual request through the Faculty
  Portal / HR office.
- Structure the answer under these headings, skipping any that genuinely
  don't apply to this request type:
  1. Eligibility
  2. Required documents
  3. Approval routing (who approves, in what order)
  4. Deadlines / timelines
  5. Notes
"""


def _generate_checklist(query_for_retrieval: str, user_facing_context: str) -> dict:
    result = _get_retrieval_pipeline().get_context(query_for_retrieval, user_role="faculty_general")
    context = result.get("context", "")
    sources = result.get("sources", [])

    context_text_only = context.replace("<doc", "").strip()
    if not context_text_only:
        return {
            "checklist": (
                "I couldn't find the relevant policy document in the knowledge base. "
                "Please check with the HR/Faculty Affairs office directly."
            ),
            "sources": [],
        }

    def _execute(client):
        return client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0.1,
            messages=[
                {"role": "system", "content": _STRUCTURING_SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": (
                        f"Request: {user_facing_context}\n\n"
                        f"Retrieved policy documents:\n{context}"
                    ),
                },
            ],
        )

    response = KeyManager.call_with_rotation(_execute, max_retries=3)
    checklist = (
        response.choices[0].message.content
        if response
        else "Unable to generate guidance right now — please try again."
    )
    return {"checklist": checklist, "sources": sources}


def _require_faculty(identity: dict):
    if not identity or identity.get("role") not in _FACULTY_ROLES:
        raise PermissionError("Only faculty members can use faculty workflow tools.")


# ── leave_application_guidance ──────────────────────────────────────────────
def handle_leave_application_guidance(identity, leave_type: str = "", **kwargs) -> dict:
    """
    Advisory-only: identifies leave type, retrieves faculty leave policy from
    the KB, and returns an eligibility + document + approval-routing checklist.
    No ERP write — the faculty member must still file leave through HR/Portal.
    """
    _require_faculty(identity)
    query = f"faculty leave application policy {leave_type}".strip()
    out = _generate_checklist(query, f"Faculty leave application ({leave_type or 'general'})")
    audit_log(identity, query="leave_application_guidance", allowed=True,
              target=identity.get("erp_id"))
    return out


# ── cpda_travel_approval_guidance ────────────────────────────────────────────
def handle_cpda_travel_approval_guidance(identity, purpose: str = "", **kwargs) -> dict:
    """
    Advisory-only: retrieves the CPDA / conference travel policy and returns
    eligibility, required documents, and approval steps. No ERP write.
    """
    _require_faculty(identity)
    query = f"CPDA conference travel approval policy {purpose}".strip()
    out = _generate_checklist(query, f"CPDA / conference travel approval ({purpose or 'general'})")
    audit_log(identity, query="cpda_travel_approval_guidance", allowed=True,
              target=identity.get("erp_id"))
    return out


# ── seed_grant_guidance ──────────────────────────────────────────────────────
def handle_seed_grant_guidance(identity, research_area: str = "", **kwargs) -> dict:
    """
    Advisory-only: retrieves the seed grant policy and returns eligibility,
    proposal structure, deadlines, and reporting obligations. No ERP write.
    """
    _require_faculty(identity)
    query = f"seed grant application policy eligibility deadlines {research_area}".strip()
    out = _generate_checklist(query, f"Seed grant application ({research_area or 'general'})")
    audit_log(identity, query="seed_grant_guidance", allowed=True,
              target=identity.get("erp_id"))
    return out
