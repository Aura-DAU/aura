"""
Wellness guardrail — lightweight distress classifier.

Runs as a pre-generation step in aura_chat.py BEFORE answer_generator.py
is ever called. When a distress signal is detected:
  - RAG retrieval is skipped entirely.
  - A fixed wellness contact block is returned instead.

Design decisions:
  - Regex-only (no LLM call) so it is instant and never fails open.
  - Errs on the side of sensitivity: a false-positive wellness response
    is far less harmful than a false-negative on a genuine cry for help.
  - Contact details mirror DAU's published counseling info as held in
    the data/student_faculty/ KB.
"""

import re

# ---------------------------------------------------------------------------
# Distress phrase patterns
# Ordered roughly from most-explicit to context-sensitive.
# All matching is case-insensitive.
# ---------------------------------------------------------------------------
_DISTRESS_PATTERNS: list[str] = [
    # Explicit self-harm / suicidal ideation
    r"\b(suicid(e|al)|kill\s+my\s*self|end\s+(my\s+)?(life|it\s+all)|want\s+to\s+die|don['\u2019]?t\s+want\s+to\s+(live|be\s+alive))\b",
    # Hopelessness / helplessness
    r"\b(hopeless|worthless|feel\s+(so\s+)?(empty|numb|broken|trapped|alone|helpless)|no\s+(reason|point)\s+to\s+(go\s+on|live|continue))\b",
    # Acute emotional crisis
    r"\b(can['\u2019]?t\s+take\s+it\s+anymore|can['\u2019]?t\s+go\s+on|falling\s+apart|breaking\s+down|mental\s+breakdown)\b",
    # Self-harm (non-suicidal)
    r"\b(self[\s\-]?harm(ing)?|cut\s+my\s*self|hurt\s+my\s*self|hurting\s+my\s*self)\b",
    # Abuse / ragging
    r"\b(being\s+(abused|ragged|harassed|bullied)|ragging|sexual\s+harassment|assault)\b",
    # Explicit requests for crisis help
    r"\b(need\s+(emergency\s+)?help\s+(now|immediately|urgently)|in\s+(a\s+)?(crisis|danger))\b",
]

_COMPILED: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE | re.UNICODE) for p in _DISTRESS_PATTERNS
]

# ---------------------------------------------------------------------------
# Wellness contact block returned when distress is detected.
# Sources: DAU published counseling info and POSH / anti-ragging contacts
# from data/student_faculty/ KB.
# ---------------------------------------------------------------------------
WELLNESS_RESPONSE = """\
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
| **iCall (national helpline)** | 9152987821 |
| **Vandrevala Foundation** | 1860-2662-345 (24×7) |

You are not alone, and it is okay to ask for help. \
If you are in immediate danger, please call campus security or go to the nearest \
hospital emergency room right away.

AURA is not equipped to provide crisis counseling. \
Please reach out to one of the contacts above.\
"""


class WellnessGuardrail:
    """
    Lightweight regex-based classifier that detects distress signals.

    Usage in aura_chat.py::

        from pipeline.guardrails.wellness_guardrail import WellnessGuardrail

        self.wellness_guardrail = WellnessGuardrail()

        # Inside chat() — before answer_generator runs:
        if self.wellness_guardrail.is_distress(query):
            return self.wellness_guardrail.wellness_response()
    """

    def is_distress(self, query: str) -> bool:
        """
        Return True if the query contains a distress signal.

        Fails CLOSED: any exception during pattern matching returns True
        so the wellness block is shown rather than a potentially harmful
        RAG answer.
        """
        try:
            for pattern in _COMPILED:
                if pattern.search(query):
                    return True
            return False
        except Exception:
            # Regex failure → default to safe / wellness path
            return True

    def wellness_response(self) -> dict:
        """
        Return the standard wellness contact block in the same shape
        as a normal AuraChat.chat() response so callers need no special-casing.
        """
        return {
            "answer": WELLNESS_RESPONSE,
            "sources": [],
            "is_personal_data": False,
            "wellness_escalation": True,   # flag for frontend / analytics
        }
