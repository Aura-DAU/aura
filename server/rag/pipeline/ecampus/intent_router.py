"""
Classifies whether a query needs the eCampus tool/orchestrator path (live,
person-specific data) or should continue through the existing general-
knowledge RAG pipeline in aura_chat.py. This is the one new decision point
inserted into aura_chat.py — everything else in that file is untouched.

Kept deliberately narrow: a cheap, fast, single-word classification call,
same pattern as QueryGuardrail.
"""

import os
from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter


class PersonalDataIntentRouter:
    def __init__(self):
        load_dotenv()
        self.client = InferenceRouter.get_client()
        self.model = os.getenv("VLLM_MODEL", os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ"))
        self.system_prompt = """
Classify the user's query as PERSONAL_DATA or GENERAL.

PERSONAL_DATA: the user is asking about their own (or, if they are faculty,
a specific named student's) CGPA, grades, attendance, fee dues, hostel
allocation, registration status, course adjustments, personal timetable, or
a faculty member's teaching schedule. Also PERSONAL_DATA: requests to link,
unlink, or check the status of an eCampus account; requests to share or
revoke sharing of academic data with a faculty member; requests to refresh
cached personal data; and requests to change, add, remove, or undo a change
to their OWN timetable (e.g. "move my 5pm class to Room 204", "add a lab on
Friday", "undo that timetable change I made yesterday").

GENERAL: anything about public university information — policies (including
the attendance policy's percentage threshold as a general rule, not the
user's own attendance number), faculty bios, admissions, events, campus
facilities, course catalogs, club info, placement statistics in aggregate,
scholarship eligibility RULES (not "am I eligible"), and any greeting or
meta question about AURA itself.

If genuinely ambiguous, prefer GENERAL — the existing RAG pipeline is safer
to fall back to than the tool-calling path, since the personal-data tools
have to actively check eligibility/consent if invoked at all.

Return exactly one word: PERSONAL_DATA or GENERAL.
"""

    def is_personal_data_query(self, query: str) -> bool:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt.strip()},
                    {"role": "user", "content": query},
                ],
                max_tokens=5,
                temperature=0.0,
            )
            return "PERSONAL_DATA" in (resp.choices[0].message.content or "").strip().upper()
        except Exception:
            # Fail toward GENERAL/RAG, never silently fail toward the
            # personal-data path on an error.
            return False
