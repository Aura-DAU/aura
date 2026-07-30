"""
Shared helpers for read-only KB retrieval skills.

Used by domain skill modules (academic, admin/people, research/careers,
campus info). Mirrors the retrieval + LLM pattern in community_tools.py.
"""

import os
from dotenv import load_dotenv
from pipeline.key_manager import KeyManager
from ..personal_data.audit import audit_log

load_dotenv()

_retrieval = None

STUDENT_ROLES = ("student", "guest")
FACULTY_ROLES = (
    "faculty", "faculty_general", "faculty_coord",
    "faculty_convenor_ug", "faculty_convenor_pg",
    "dean_faculty", "dean_academic", "superadmin",
)
PUBLIC_READER_ROLES = STUDENT_ROLES + FACULTY_ROLES


def identity_payload(identity) -> dict:
    if identity is None:
        return {}
    if isinstance(identity, dict):
        return identity
    return getattr(identity, "as_dict", lambda: {})()


def identity_role(identity) -> str | None:
    payload = identity_payload(identity)
    if not payload:
        return None
    return payload.get("role")


def require_role(identity, allowed: tuple[str, ...], message: str) -> None:
    role = identity_role(identity)
    if role not in allowed:
        raise PermissionError(message)


def get_retrieval_pipeline():
    global _retrieval
    if _retrieval is None:
        from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
        _retrieval = RetrievalPipeline()
    return _retrieval


def run_kb_query(
    query: str,
    user_role: str,
    system_prompt: str,
    user_message: str,
    request_context=None,
    empty_response: str | None = None,
) -> dict:
    """Retrieve KB context and summarize with the LLM. Read-only."""
    academic_scope = getattr(request_context, "academic_scope", None) if request_context else None
    pipeline = get_retrieval_pipeline()
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
        return {
            "response": empty_response or (
                "I couldn't find that in the knowledge base. Try a more specific "
                "name or keyword, or ask via general campus search."
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


def audit(identity, tool_name: str, target: str = "") -> None:
    audit_log(identity_payload(identity), query=tool_name, allowed=True, target=target or "n/a")
