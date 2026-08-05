# Classifies whether a query needs the eCampus tool/orchestrator path (live
# person-specific data or public KB tools) or should continue through the
# existing general RAG flow in aura_chat / aura_chat_graph.
# Same pattern as QueryGuardrail.

import logging
import os
import re
from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter
from pipeline.generation.answer_generator import log_soft_failure
# Single source of truth for "the query names a cohort" (programme/branch/
# year/sem/section) — the 2026-08 hotfix guard in the personal classifier.
from personal_query_classifier import PUBLIC_PROGRAMME_OVERRIDE_PAT

logger = logging.getLogger(__name__)

# Deterministic fast-path for first-person timetable/schedule reads. Phrasings
# like "what is my time table?" (two words), "display my timetable", or "my
# class schedule today" were intermittently classified GENERAL by the LLM,
# which degrades the query to public RAG — where the generator truthfully
# answers "I don't have access to your timetable in the provided context".
# The requester's own schedule is always PERSONAL_DATA (get_my_timetable /
# get_my_teaching_schedule exist for exactly this), so decide it without an
# LLM round-trip — same pattern as the calendar gates in aura_chat_graph.
# Queries that also name a cohort (year/sem/branch/section) are left to the
# LLM so the COMMUNITY named-cohort rule below still applies.
_OWN_SCHEDULE_PAT = re.compile(
    r"\bmy\s+(?:time\s*table|(?:class\s+|teaching\s+)?schedule|classes)\b"
    r"|\bwhat\s+classes\s+do\s+i\s+have\b"
    r"|\bdo\s+i\s+have\s+(?:any\s+)?(?:class(?:es)?|labs?|lectures?|tutorials?)\b",
    re.IGNORECASE,
)


class PersonalDataIntentRouter:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv("VLLM_MODEL", os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ"))
        self.system_prompt = """
Classify the user's query as PERSONAL_DATA, COMMUNITY, or GENERAL.

PERSONAL_DATA: the user is asking about their own (or, if they are faculty,
a specific named student's) CGPA, grades, attendance, fee dues, hostel
allocation, registration status, course adjustments, or electives. The
requester's OWN class timetable is PERSONAL_DATA in every phrasing — AURA
has a live tool for it, so these must never go to GENERAL: "timetable",
"time table" (two words), "schedule", "my classes". Examples (all
PERSONAL_DATA): "What is my time table?", "can you display my time table",
"show my timetable", "my class schedule today", "what classes do I have
tomorrow". A faculty member's own teaching schedule is likewise
PERSONAL_DATA. Also PERSONAL_DATA: requests to link,
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
- The class timetable/schedule for a NAMED cohort — a specific year/semester
  + branch + section, e.g. "give me the timetable of BTech ICT 3rd sem
  section A" or "schedule for 2nd year MnC section B". A request that names
  a year/sem/branch/section is COMMUNITY even if it says "my" and the
  requester happens to be in that cohort; a first-person request with NO
  cohort named ("what is my time table?") is PERSONAL_DATA.
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
only when the query names no personal record at all — a first-person
timetable/schedule/grades/attendance/fees request is always PERSONAL_DATA
(the personal-data tools enforce eligibility and consent themselves).

Return exactly one word: PERSONAL_DATA, COMMUNITY, or GENERAL.
"""

    def classify(self, query: str) -> str:
        """Return PERSONAL_DATA | COMMUNITY | GENERAL. Fail toward GENERAL."""
        # First-person schedule reads never depend on the LLM verdict — see
        # _OWN_SCHEDULE_PAT. Without this, a classifier outage (which fails
        # toward GENERAL by design) silently degrades "what is my time table?"
        # to public RAG and a false "I don't have access" answer.
        if _OWN_SCHEDULE_PAT.search(query) and not PUBLIC_PROGRAMME_OVERRIDE_PAT.search(query):
            return "PERSONAL_DATA"
        model = self.model
        system = self.system_prompt.strip()
        dispatch = {"node": None}
        try:
            def _execute(client):
                dispatch["node"] = str(getattr(client, "base_url", "") or "") or None
                return client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=8,
                    temperature=0.0,
                    extra_body=InferenceRouter.no_think_extra_body(),
                )

            resp = InferenceRouter.call_with_rotation(_execute, max_retries=3)
            raw = (resp.choices[0].message.content or "").strip().upper()
            if "PERSONAL_DATA" in raw or "PERSONAL DATA" in raw:
                return "PERSONAL_DATA"
            # PUBLIC_KB is an accepted synonym for the community/public-KB path.
            if "COMMUNITY" in raw or "PUBLIC_KB" in raw or "PUBLIC KB" in raw:
                return "COMMUNITY"
            if raw not in ("GENERAL",):
                # A GENERAL returned because the model said something we could
                # not parse is a different event from a GENERAL the model
                # actually chose, and only the former is a defect.
                log_soft_failure(
                    "AURA-ROUTE-002",
                    "intent_router.classify",
                    node=dispatch["node"],
                    log=logger,
                    detail="unparsed classifier output, defaulted to GENERAL",
                    raw=raw[:80],
                )
            return "GENERAL"
        except Exception as exc:
            # Fail toward GENERAL/RAG, never silently fail toward a tool path.
            # The direction is deliberate, but it must not be silent: an
            # unreachable classifier degrades every COMMUNITY query to plain RAG
            # (skipping lookup_academic_requirements) with no other symptom.
            log_soft_failure(
                "AURA-ROUTE-001",
                "intent_router.classify",
                exc=exc,
                node=dispatch["node"],
                log=logger,
                degraded_to="GENERAL",
            )
            return "GENERAL"

    def is_personal_data_query(self, query: str) -> bool:
        return self.classify(query) == "PERSONAL_DATA"

    def is_community_query(self, query: str) -> bool:
        return self.classify(query) == "COMMUNITY"
