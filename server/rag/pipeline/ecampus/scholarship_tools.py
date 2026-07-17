"""
Scholarship eligibility screening — advisory-only, KB-retrieval-driven.

screen_scholarship_eligibility: cross-references a student's own profile
attributes (branch, year, category, cgpa, annual_income) against the
scholarship/financial-aid rules retrieved from the KB, and returns a
structured list of schemes with eligibility status. AURA never submits an
application or verifies documents itself — this is guidance only, same
posture as every other *_guidance tool in this package.

Follows the same pattern as student_workflow_tools.py / community_tools.py:
retrieval via RetrievalPipeline, LLM call routed through KeyManager so it
participates in Groq key rotation like every other pipeline component
(no direct `Groq(api_key=...)` client — that bypasses rotation/backoff).
"""

import os
import json
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


_SCHOLARSHIP_SYSTEM_PROMPT = """
You are AURA's scholarship screening assistant. Using ONLY the retrieved
DAU scholarship/financial-aid policy context below, cross-reference the
named schemes against the student's profile and return a structured
eligibility assessment.

Rules:
- Use ONLY schemes and criteria mentioned in the retrieved context. Never
  invent a scheme, amount, or eligibility rule that isn't in the text.
- If the retrieved context does not cover a scheme's criteria in enough
  detail to decide, mark it "conditionally_eligible" and explain what's
  missing rather than guessing "eligible" or "ineligible".
- This is advisory guidance only — AURA does not submit or verify any
  scholarship application. Every response should end with a reminder to
  confirm eligibility and apply through the Academic / Accounts Office.

Output ONLY valid JSON, no markdown fences, matching this shape:
{
  "eligible_schemes": [
    {
      "name": "...",
      "type": "...",
      "benefit": "...",
      "status": "eligible" | "conditionally_eligible" | "ineligible",
      "reason_or_conditions": "...",
      "mandatory_documents": ["..."],
      "deadline": "..."
    }
  ],
  "general_guidelines": ["..."]
}
"""


def screen_scholarship_eligibility(
    identity, branch: str, year: int, category: str, cgpa: float,
    annual_income: float | None = None, **kwargs
) -> dict:
    """
    Advisory-only: retrieves scholarship/financial-aid policy from the KB
    and cross-references it against the requester's own stated profile.
    No ERP write, no application submission.
    """
    if not identity or identity.get("role") not in ("student", "guest"):
        raise PermissionError("This tool is for students screening their own eligibility.")

    query = (
        "scholarships and financial aid eligibility conditions criteria "
        "merit cum means fellowship DAFS category income CGPA"
    )
    result = _get_retrieval_pipeline().get_context(query, user_role="student")
    context = result.get("context", "")
    sources = result.get("sources", [])

    if not context.strip():
        out = {
            "eligible_schemes": [],
            "general_guidelines": [
                "I couldn't find scholarship policy details in the knowledge base — "
                "please confirm current schemes with the Academic / Accounts Office.",
            ],
            "sources": [],
        }
        audit_log(identity, query="screen_scholarship_eligibility", allowed=True,
                  target=identity.get("erp_id"))
        return out

    student_profile = (
        f"Branch/Program: {branch}\n"
        f"Current Year of Study: {year}\n"
        f"Admission Category: {category}\n"
        f"Current CGPA/CPI: {cgpa}\n"
        f"Annual Family Income (INR): {annual_income if annual_income is not None else 'Not provided'}"
    )

    def _execute(client):
        return client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0,
            messages=[
                {"role": "system", "content": _SCHOLARSHIP_SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": (
                        f"Student profile:\n{student_profile}\n\n"
                        f"Retrieved policy context:\n{context}"
                    ),
                },
            ],
        )

    response = KeyManager.call_with_rotation(_execute, max_retries=3)
    raw = response.choices[0].message.content.strip() if response else ""
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = {}

    if not isinstance(parsed.get("eligible_schemes"), list):
        parsed["eligible_schemes"] = []
    if not isinstance(parsed.get("general_guidelines"), list):
        parsed["general_guidelines"] = [
            "Not specified in the retrieved policy documents — confirm with the "
            "Academic / Accounts Office."
        ]

    parsed["sources"] = sources
    audit_log(identity, query=f"screen_scholarship_eligibility:{branch}:{category}",
              allowed=True, target=identity.get("erp_id"))
    return parsed
