# Wellness guardrail — detects signs of distress in a query BEFORE it reaches
# answer_generator / the RAG pipeline, and routes to a fixed, human-reviewed
# this class; that hunk was intentionally NOT applied — see review notes.)

import os
import re
from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter

load_dotenv()

# ---------------------------------------------------------------------------
# Fixed, human-reviewed contact block.
# Do NOT have the LLM generate this text.
# Update contact details here only after confirming with the counseling
# center / student welfare office. Sources: DAU published counseling info
# and POSH / anti-ragging contacts from data/student_faculty/ KB.
# ---------------------------------------------------------------------------
WELLNESS_CONTACT_BLOCK = """\
I'm really glad you reached out. What you're sharing sounds serious, \
and you deserve real support — not just information.

**Please connect with someone who can help you right now:**

| Contact | Details |
|---|---|
| **DAU Counseling Centre** | counselling@dau.ac.in |
| **Dean of Students Office** | dean_students@dau.ac.in |
| **Anti-Ragging Helpline** | anti_ragging@dau.ac.in |
| **POSH Committee** | posh@dau.ac.in |
| **Security / Emergency** | +91-79-6847-9000 (campus) |
| **iCall / TISS helpline** | 9152987821 (Mon–Sat, 8 am–10 pm) — free, confidential |
| **AASRA (24×7 crisis)** | 91-9820466726 |

You are not alone, and it is okay to ask for help. \
If you are in immediate danger, please call campus security or go to the \
nearest hospital emergency room right away.

AURA is not equipped to provide crisis counseling. \
Please reach out to one of the contacts above.
"""

# ---------------------------------------------------------------------------
# Lightweight keyword fallback — intentionally coarse.
# Fires ONLY when the LLM classifier is unreachable.
# The LLM path is the primary detector and handles nuance and phrasing
# that a keyword list cannot. Do not expand this list as a substitute
# for the LLM — fix the LLM integration instead.
# ---------------------------------------------------------------------------
_FALLBACK_UNCONDITIONAL_PATTERNS: list[str] = [
    r"\bsuicid",
    r"\bkill\s+my\s*self\b",
    r"\bend\s+(my\s+)?(life|it\s+all)\b",
    r"\bself[\s\-]?harm",
    r"\bhurt(ing)?\s+my\s*self\b",
    r"\bcut(ting)?\s+my\s*self\b",
    r"\bwant\s+to\s+die\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bdon['\u2019]?t\s+want\s+to\s+(live|be\s+alive)\b",
]

# Everyday academic-stress idiom that also reads as distress in isolation.
# Kept in the fallback, but suppressed when the query carries academic framing
# \u2014 see _fallback_check.
_FALLBACK_CONTEXTUAL_PATTERNS: list[str] = [
    r"\bcan['\u2019]?t\s+(take(\s+it)?|go\s+on|cope)(\s+anymore)?\b",
]

_FALLBACK_DISTRESS_PATTERNS: list[str] = (
    _FALLBACK_UNCONDITIONAL_PATTERNS + _FALLBACK_CONTEXTUAL_PATTERNS
)


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]


_FALLBACK_UNCONDITIONAL_COMPILED = _compile(_FALLBACK_UNCONDITIONAL_PATTERNS)
_FALLBACK_CONTEXTUAL_COMPILED = _compile(_FALLBACK_CONTEXTUAL_PATTERNS)
_FALLBACK_COMPILED: list[re.Pattern[str]] = _compile(
    _FALLBACK_DISTRESS_PATTERNS
)

_ACADEMIC_CONTEXT = re.compile(
    r"\b(assignment|deadline|submission|exam|quiz|midsem|endsem|syllabus|"
    r"workload|course|credit|elective|semester|registration|attendance|"
    r"fee|hostel|mess|timetable|lab|project|placement|internship|"
    r"drop|withdraw|backlog|grade|cgpa|spi|cpi)\b",
    re.IGNORECASE | re.UNICODE,
)

# ---------------------------------------------------------------------------
# LLM system prompt for the classifier call.
# Output contract: exactly one token — DISTRESS or NOT_DISTRESS.
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """
You are a safety classifier for a university assistant. Classify the user's
message as DISTRESS or NOT_DISTRESS.

DISTRESS means the message expresses suicidal ideation, self-harm intent,
severe hopelessness, or a mental health crisis needing human support right
now — not academic stress phrased casually ("this exam is killing me").

Output exactly one word: DISTRESS or NOT_DISTRESS. No punctuation, no
explanation.
""".strip()


class WellnessGuardrail:
    # LLM-based distress classifier with a keyword-regex fallback.
    # Primary path — Groq LLM call: handles nuanced, paraphrased, and
    # }

    def __init__(self) -> None:
        self.client = InferenceRouter.get_client()
        # llama-3.3-70b-versatile: fast, instruction-following, available on Groq.
        # Override via VLLM_WELLNESS_MODEL env var if needed.
        # Falls back to VLLM_MODEL (the pool's served id) before the hardcoded
        # default, matching every other call site. Without that link this
        # guardrail asked for a model the pool doesn't serve, 404'd, and
        # silently degraded to the keyword fallback on every request.
        self.model = os.getenv(
            "VLLM_WELLNESS_MODEL",
            os.getenv(
                "GROQ_WELLNESS_MODEL",
                os.getenv("VLLM_MODEL", "Qwen/Qwen3-32B-AWQ"),
            ),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, query: str) -> bool:
        # Return True if the query should be routed to the wellness block.
        # Tries the LLM classifier first; falls back to keyword regex if
        # the API call fails for any reason.
        try:
            return self._llm_check(query)
        except Exception as exc:
            print(
                f"[WellnessGuardrail] LLM classification failed, using keyword fallback: {exc}"
            )
            return self._fallback_check(query)

    def get_response(self) -> str:
        # Return the fixed, human-reviewed wellness contact block.
        return WELLNESS_CONTACT_BLOCK

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _llm_check(self, query: str) -> bool:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            max_tokens=5,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            extra_body=InferenceRouter.no_think_extra_body(),
        )
        result = response.choices[0].message.content.strip().upper()
        # Guard against the model echoing "NOT_DISTRESS" which contains "DISTRESS"
        return result == "DISTRESS"

    def _fallback_check(self, query: str) -> bool:
        if any(p.search(query) for p in _FALLBACK_UNCONDITIONAL_COMPILED):
            return True
        # "I can't cope with this course load, when is the drop deadline?" is a
        # routine academic query. Firing the crisis block on it swallows the
        # answer entirely, so ambiguous phrasings count as distress only when
        # nothing in the query frames it as coursework. Unconditional patterns
        # above are checked first and are never suppressed.
        if any(p.search(query) for p in _FALLBACK_CONTEXTUAL_COMPILED):
            return _ACADEMIC_CONTEXT.search(query) is None
        return False
