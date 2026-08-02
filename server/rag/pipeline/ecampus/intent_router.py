# Classifies whether a query needs the eCampus tool/orchestrator path (live
# person-specific data or public KB tools) or should continue through the
# existing general RAG flow in aura_chat / aura_chat_graph.
# Same pattern as QueryGuardrail.

import os
from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter


class PersonalDataIntentRouter:
    def __init__(self):
        load_dotenv()
        self.client = InferenceRouter.get_client()
        self.model = os.getenv("VLLM_MODEL", os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ"))
        self.system_prompt = """
Classify the user's query as PERSONAL_DATA, COMMUNITY, or GENERAL.

PERSONAL_DATA: the user is asking about their own (or, if they are faculty,
a specific named student's) CGPA, grades, attendance, fee dues, hostel
allocation, registration status, course adjustments, personal timetable, or
a faculty member's teaching schedule. Also PERSONAL_DATA: requests to link,
unlink, or check the status of an eCampus account; requests to share or
revoke sharing of academic data with a faculty member; requests to refresh
cached personal data; and requests to change, add, remove, or undo a change
to their OWN timetable (e.g. "move my 5pm class to Room 204", "add a lab on
Friday", "undo that timetable change I made yesterday"). Personal scholarship
eligibility screening ("am I eligible for X scholarship given my CGPA") is
PERSONAL_DATA. Requests to connect, link, check, sync, export, or add the
requester's timetable/classes to their own Google Calendar are also
PERSONAL_DATA. Google Calendar actions are not academic-calendar lookups.

COMMUNITY: public campus KB tool lookups — NOT private ERP records. Includes:
- Student clubs / SBG (list clubs, purpose, how to join, published rosters,
  convenor / office-bearers / club email) and campus event club-registration
  guidance.
- Faculty/institutional governance committee ToR.
- Faculty / staff / people directory: "who is X", bare name, faculty profile,
  search people by department/role.
- Academic calendar / deadlines, course policy for a named course, program
  academic requirements, admissions info, published public timetable docs.
- The class timetable/schedule for a NAMED cohort that is not phrased as
  the requester's own — a specific year/semester + branch + section, e.g.
  "give me the timetable of BTech ICT 3rd sem section A" or "schedule for
  2nd year MnC section B". Only "my timetable" / "my schedule" (no cohort
  named) is PERSONAL_DATA — a request that names its own year/sem/branch/
  section is COMMUNITY even if the requester happens to be in that cohort.
- University / administration policies (attendance rules, fees policy,
  anti-ragging, hostel allotment rules — the RULE, not the user's own dues).
- Research areas/labs/policies, placements/careers info, campus events and
  notices, facilities/infrastructure, student services, alumni, achievements,
  Continuing Education (CEP).
Examples: "what clubs for music", "who is the convenor of Programming Club",
"Who is Aditya Tatu?", "Aditya Tatu", "when is mid-sem", "BTech ICT admissions",
"placement statistics", "hostel facilities", "anti-ragging policy",
"give me timetable of BTech ICT 3rd sem sec A", "schedule for 2nd year MnC section B".

GENERAL: greetings, thanks, meta questions about AURA itself, short follow-ups
with no topic of their own, and queries too vague to map to a campus tool
(prefer RAG). Do NOT put faculty who-is / campus directory / clubs /
academic-calendar dates / admissions / placements / facilities questions here
— those are COMMUNITY. Do not apply that academic-calendar rule to requests
about the user's connected Google Calendar.

If genuinely ambiguous between COMMUNITY and GENERAL, prefer COMMUNITY when
any campus KB domain above is involved. Prefer GENERAL over PERSONAL_DATA
when unsure — the personal-data tools must check eligibility/consent if
invoked at all.

Return exactly one word: PERSONAL_DATA, COMMUNITY, or GENERAL.
"""

    def classify(self, query: str) -> str:
        """Return PERSONAL_DATA | COMMUNITY | GENERAL. Fail toward GENERAL."""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt.strip()},
                    {"role": "user", "content": query},
                ],
                max_tokens=8,
                temperature=0.0,
            )
            raw = (resp.choices[0].message.content or "").strip().upper()
            if "PERSONAL_DATA" in raw or "PERSONAL DATA" in raw:
                return "PERSONAL_DATA"
            # PUBLIC_KB is an accepted synonym for the community/public-KB path.
            if "COMMUNITY" in raw or "PUBLIC_KB" in raw or "PUBLIC KB" in raw:
                return "COMMUNITY"
            return "GENERAL"
        except Exception:
            # Fail toward GENERAL/RAG, never silently fail toward a tool path.
            return "GENERAL"

    def is_personal_data_query(self, query: str) -> bool:
        return self.classify(query) == "PERSONAL_DATA"

    def is_community_query(self, query: str) -> bool:
        return self.classify(query) == "COMMUNITY"
