"""
Student workflow tools — advisory-only guidance, no writes anywhere.

certificate_request_guidance: bonafide / transcript / ID-card procedures,
retrieved from the KB and returned as a step-by-step checklist.

hostel_complaint_guidance: captures a complaint type conversationally and
returns a summary + the correct contact — never files a ticket itself
(no ticketing-system write path exists or is planned).
"""

import os
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


def _get_retrieval_pipeline():
    global _retrieval
    if _retrieval is None:
        from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
        _retrieval = RetrievalPipeline()
    return _retrieval

_CERT_SYSTEM_PROMPT = """
You are AURA's student services assistant. Turn retrieved DAU procedure
documents into a short step-by-step checklist for requesting a document
(bonafide certificate, transcript, ID card, or similar).

Rules:
- Use ONLY the retrieved context. Never invent processing times, fees, or
  office names not present in the text.
- If a detail isn't in the retrieved context, say "Not specified in the
  retrieved documents" rather than guessing.
- Structure as: 1) Where to apply  2) Documents needed  3) Processing time
  4) Fee (if any)  5) Notes.
- AURA cannot submit this request — end with a reminder to file it through
  the Student Services Portal or the relevant office in person.
"""

_HOSTEL_SYSTEM_PROMPT = """
You are AURA's hostel support assistant. The student has described a hostel
complaint. Using ONLY the retrieved hostel policy/contact context:

- Summarize the complaint back in one or two sentences so the student can
  confirm you understood it correctly.
- Name the correct contact (warden, hostel office, maintenance desk, etc.)
  if the retrieved context identifies one.
- Do NOT claim to have filed, logged, or escalated anything — AURA has no
  ticketing write path. Tell the student explicitly that they need to
  raise it themselves through the hostel office / warden / official
  channel, and give that contact if known.
"""


def _run_checklist(query: str, system_prompt: str, user_message: str, request_context=None) -> dict:
    academic_scope = getattr(request_context, "academic_scope", None) if request_context else None
    pipeline = _get_retrieval_pipeline()
    try:
        result = pipeline.get_context(
            query,
            user_role="student",
            academic_scope=academic_scope,
        )
    except TypeError:
        result = pipeline.get_context(query, user_role="student")
    context = result.get("context", "")
    sources = result.get("sources", [])

    if not context.strip():
        return {
            "response": (
                "I couldn't find the relevant procedure in the knowledge base. "
                "Please check with the Student Services office directly."
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


# ── certificate_request_guidance ────────────────────────────────────────────
def handle_certificate_request_guidance(identity, document_type: str = "", request_context=None, **kwargs) -> dict:
    """Advisory-only checklist for requesting bonafide / transcript / ID-card. No writes."""
    role = _identity_role(identity)
    if role not in ("student", "guest"):
        raise PermissionError("This tool is for students requesting their own documents.")
    query = f"how to request {document_type or 'bonafide certificate transcript ID card'} procedure"
    out = _run_checklist(
        query, _CERT_SYSTEM_PROMPT,
        f"Student wants to request: {document_type or 'a document (unspecified type)'}",
        request_context=request_context,
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="certificate_request_guidance", allowed=True,
              target=payload.get("erp_id"))
    return out


# ── hostel_complaint_guidance ────────────────────────────────────────────────
def handle_hostel_complaint_guidance(identity, complaint_type: str = "", complaint_detail: str = "", request_context=None, **kwargs) -> dict:
    """Advisory-only: summarizes complaint + names contact. Never files a ticket."""
    role = _identity_role(identity)
    if role not in ("student", "guest"):
        raise PermissionError("This tool is for students reporting their own hostel issue.")
    query = f"hostel complaint {complaint_type} contact warden maintenance procedure"
    out = _run_checklist(
        query, _HOSTEL_SYSTEM_PROMPT,
        f"Complaint type: {complaint_type or 'unspecified'}. Details: {complaint_detail or 'none given'}",
        request_context=request_context,
    )
    payload = _identity_payload(identity)
    audit_log(payload, query="hostel_complaint_guidance", allowed=True,
              target=payload.get("erp_id"))
    return out
