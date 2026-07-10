"""
Wellness guardrail — detects signs of distress in a query BEFORE it reaches
answer_generator / the RAG pipeline, and routes to a fixed, human-reviewed
wellness-contact block instead of a generated answer.

This is deliberately NOT an LLM-generated response for the distress case
itself — the contact block is fixed and human-reviewed so AURA never
improvises in a safety-critical moment. The LLM call here is used only to
CLASSIFY (distress / not distress), matching query_guardrail.py's pattern.

Fails OPEN for the classification step (same as QueryGuardrail.is_safe):
if the guardrail LLM is unavailable, we do not silently swallow a
potentially distressed message — we fall back to a lightweight keyword
check so we never regress to "no safety net at all".
"""

import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Fixed, human-reviewed response — do not have the LLM generate this text.
# Update contact details here only after confirming with the counseling
# center / student welfare office; keep this list short and accurate.
WELLNESS_CONTACT_BLOCK = """\
I'm really glad you reached out, and I want to make sure you get support \
from people who are equipped to help.

- **DAU Counseling Center**: available for confidential, in-person and \
  telehealth support — contact the Student Welfare office to book a session.
- **Campus emergency / security desk**: for anything urgent, right now.
- **iCall (TISS) helpline**: 9152987821 (Mon–Sat, 8am–10pm) — free, \
  confidential psychosocial support.
- **AASRA**: 91-9820466726 (24x7) — crisis helpline.

You don't have to handle this alone, and reaching out is a good step. \
Would you like me to also share DAU's on-campus counseling contact details?
"""

# Lightweight fallback keyword list — intentionally coarse. This only fires
# if the LLM classifier is unreachable; the LLM path above is the primary
# detector and handles nuance/phrasing the keyword list can't.
_FALLBACK_DISTRESS_PATTERNS = [
    r"\bsuicid", r"\bkill myself\b", r"\bend my life\b", r"\bself[\s-]?harm",
    r"\bhurt myself\b", r"\bwant to die\b", r"\bno reason to live\b",
    r"\bcan'?t (take|go on|cope) anymore\b",
]

_SYSTEM_PROMPT = """
You are a safety classifier for a university assistant. Classify the user's
message as DISTRESS or NOT_DISTRESS.

DISTRESS means the message expresses suicidal ideation, self-harm intent,
severe hopelessness, or a mental health crisis needing human support right
now — not academic stress phrased casually ("this exam is killing me").

Output exactly one word: DISTRESS or NOT_DISTRESS. No punctuation, no
explanation.
"""


class WellnessGuardrail:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def _fallback_check(self, query: str) -> bool:
        q = query.lower()
        return any(re.search(p, q) for p in _FALLBACK_DISTRESS_PATTERNS)

    def check(self, query: str) -> bool:
        """Returns True if the query should be routed to the wellness block."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                max_tokens=5,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": query},
                ],
            )
            result = response.choices[0].message.content.strip().upper()
            return "DISTRESS" in result and "NOT_DISTRESS" not in result
        except Exception as e:
            print(f"[WellnessGuardrail] LLM classification failed, using fallback: {e}")
            return self._fallback_check(query)

    def get_response(self) -> str:
        return WELLNESS_CONTACT_BLOCK
