import json
import logging
import os
import re

from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter

logger = logging.getLogger(__name__)

# The plan is a small JSON object; an uncapped completion can run to the end of
# the context window when the model misbehaves.
_PLANNER_MAX_TOKENS = int(os.getenv("AURA_PLANNER_MAX_TOKENS", "600"))


SYSTEM_PROMPT = """
You are the retrieval planner for AURA, the assistant for Dhirubhai Ambani University (DAU).
Analyse the user query and return ONE JSON object, with no other text.

# Output schema (every field is required)
{
  "category": one of faculty | academics | admissions | events | research | campus_life | administration | alumni | general,
  "intent": one of overview | eligibility | contact | research | location | event_details | admission_process | scholarship | rules | facilities | general,
  "retrieval_intent": one of faculty_profile | faculty_research | faculty_contact | alumni_profile | program_overview | program_eligibility | program_curriculum | admissions_information | scholarship_information | event_information | event_version | policy_version | rules | general,
  "entity_confidence": number 0.0-1.0 (0.0 when no entities),
  "multi_entity_query": boolean,
  "entities": object ({} when none),
  "query_decomposition": list of short retrieval queries, or null,
  "retrieval_hints": {"required_sections": [...]} or {},
  "is_claim_verification": boolean,
  "requires_complete_list": boolean,
  "expanded_terms": list of at most 5 strings ([] when not needed)
}

# Entities
Keys: person_name, designation, event_name, program_name, department_name, scholarship_name, course_code, course_name, semester, rule_year.
- Extract only what the query states; never invent. Several values of one type → an array.
- Course codes (IT205, CS301, ICT623) are always course_code.
- A job title without a name ("Sports Officer", "Warden", "Chief Proctor") goes in designation and, verbatim, in retrieval_hints.required_sections. Never replace it with the committee it belongs to.
- A named academic year ("2024-25") goes in rule_year.
- Year is not semester: 1st year = semesters 1 and 2, 2nd = 3 and 4, 3rd = 5 and 6, 4th = 7 and 8. "3rd year" → semester ["5", "6"].

# Retrieval intent guidance
- policy_version: when a policy was issued or became effective, what it supersedes, whether a newer version exists.
- rules: exam regulations, malpractice, conduct, discipline, progression rules (credit limits, CPI, DX grade), what is or is not allowed.
- event_version: comparing annual editions of an event.
- Fees and seats → admissions_information with required_sections such as "Fee", "Fees Structure", "Tuition".

# Other fields
- multi_entity_query + query_decomposition: for comparisons or several topics, one focused retrieval query per side or topic. Otherwise false and null.
- is_claim_verification: true when the user asks to confirm something they heard ("my friend said X, is it true?").
- requires_complete_list: true for "which is NOT", "how many", "list all", or a request for the full content of one named document (a course file, a whole policy, a full syllabus).
- expanded_terms: formal document wording for colloquial phrasing ("who washes clothes in hostel" → "laundry service", "dhobi"). Empty when the query is already formal. Never guess the meaning of an unknown acronym; if a short term has a plain English meaning ("cot" = bed), use that.

# Examples
Query: Who is Abhishek Jindal?
{"category":"faculty","intent":"overview","retrieval_intent":"faculty_profile","entity_confidence":0.98,"multi_entity_query":false,"entities":{"person_name":"Abhishek Jindal"},"query_decomposition":null,"retrieval_hints":{},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: What is the mail id of the sports officer?
{"category":"faculty","intent":"contact","retrieval_intent":"faculty_contact","entity_confidence":0.9,"multi_entity_query":false,"entities":{"designation":"Sports Officer"},"query_decomposition":null,"retrieval_hints":{"required_sections":["Sports Officer","Officers and Staff","Contact"]},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: Compare BTech CSAI and BTech ICT
{"category":"academics","intent":"overview","retrieval_intent":"program_overview","entity_confidence":0.95,"multi_entity_query":true,"entities":{"program_name":["BTech CSAI","BTech ICT"]},"query_decomposition":["BTech CSAI overview","BTech ICT overview"],"retrieval_hints":{},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: What courses are offered in Semester 3 and Semester 4 of BTech ICT?
{"category":"academics","intent":"overview","retrieval_intent":"program_curriculum","entity_confidence":0.97,"multi_entity_query":true,"entities":{"program_name":"BTech ICT","semester":["III","IV"]},"query_decomposition":["BTech ICT Semester III courses","BTech ICT Semester IV courses"],"retrieval_hints":{},"is_claim_verification":false,"requires_complete_list":true,"expanded_terms":[]}

Query: What is the fee for BS-MS program?
{"category":"admissions","intent":"overview","retrieval_intent":"admissions_information","entity_confidence":0.93,"multi_entity_query":false,"entities":{"program_name":"BS-MS"},"query_decomposition":null,"retrieval_hints":{"required_sections":["Fee","Fees Structure","Tuition"]},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: Does a DX grade make a student ineligible for a merit scholarship?
{"category":"academics","intent":"eligibility","retrieval_intent":"scholarship_information","entity_confidence":0.87,"multi_entity_query":true,"entities":{"scholarship_name":"merit scholarship"},"query_decomposition":["DX grade definition and consequences","merit scholarship eligibility criteria"],"retrieval_hints":{"required_sections":["DX","Scholarship","Eligibility"]},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: A friend told me attendance is tracked overall not per course. Is that true?
{"category":"academics","intent":"rules","retrieval_intent":"rules","entity_confidence":0.0,"multi_entity_query":false,"entities":{},"query_decomposition":null,"retrieval_hints":{"required_sections":["Attendance","Academic Policy"]},"is_claim_verification":true,"requires_complete_list":false,"expanded_terms":[]}

Query: Does the Patent Filing Policy mention which earlier policy it supersedes?
{"category":"research","intent":"overview","retrieval_intent":"policy_version","entity_confidence":0.82,"multi_entity_query":false,"entities":{},"query_decomposition":null,"retrieval_hints":{"required_sections":["Version History","Supersedes","Effective Date","Patent"]},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":[]}

Query: who washes clothes in the hostel
{"category":"campus_life","intent":"facilities","retrieval_intent":"general","entity_confidence":0.0,"multi_entity_query":false,"entities":{},"query_decomposition":null,"retrieval_hints":{"required_sections":["Hostel","Laundry"]},"is_claim_verification":false,"requires_complete_list":false,"expanded_terms":["laundry service","dhobi","linen"]}
"""

SEMESTER_MAP = {
    "1": 1, "i": 1, "1st": 1, "first": 1,
    "2": 2, "ii": 2, "2nd": 2, "second": 2,
    "3": 3, "iii": 3, "3rd": 3, "third": 3,
    "4": 4, "iv": 4, "4th": 4, "fourth": 4,
    "5": 5, "v": 5, "5th": 5, "fifth": 5,
    "6": 6, "vi": 6, "6th": 6, "sixth": 6,
    "7": 7, "vii": 7, "7th": 7, "seventh": 7,
    "8": 8, "viii": 8, "8th": 8, "eighth": 8,
}
ROMAN_SEMESTER_MAP = {
    1: "I", 2: "II", 3: "III", 4: "IV",
    5: "V", 6: "VI", 7: "VII", 8: "VIII"
}

# Issue 3 fix (Course Code <-> Title Resolution): the timetable data is
# strictly keyed by course_code (see server/rag/pipeline/timetable/service.py),
# but users ask timetable questions using the informal course *name*
# ("Machine Learning") rather than the code ("IT608"). Left unresolved, the
# course_name entity never matches timetable rows and the query fails.
#
# Built from the official course catalog (data/academics/course_catalog_v2.md)
# so codes are never guessed -- only names the catalog itself binds to a code
# are included here.
COURSE_NAME_TO_CODE = {
    "introduction to programming": ["IT112", "IT603"],
    "data structures and algorithms": ["IT205", "IT623"],
    "data structures": ["IT205", "IT623"],
    "design and analysis of algorithms": ["IT216"],
}


def resolve_course_name_to_code(query: str, entities: dict) -> dict:
    """Resolve an informal course_name entity ('Data Structures') to its exact
    course_code(s) via COURSE_NAME_TO_CODE, so timetable lookups keyed by code
    don't fail on natural-language course names. Never overrides a course_code
    the planner already extracted."""
    if not entities or entities.get("course_code"):
        return entities

    course_name = entities.get("course_name")
    candidates = []
    if isinstance(course_name, list):
        candidates.extend(c for c in course_name if c)
    elif course_name:
        candidates.append(course_name)
    if not candidates and query:
        candidates.append(query)

    for candidate in candidates:
        cand_lower = str(candidate).strip().lower()
        if not cand_lower:
            continue
        for name, codes in COURSE_NAME_TO_CODE.items():
            # The catalogue name must appear whole; a fragment like "data"
            # must not map to "data structures".
            if name in cand_lower:
                entities["course_code"] = codes if len(codes) > 1 else codes[0]
                return entities

    return entities


def canonicalize_informal_semester(query: str, entities: dict) -> dict:
    """Parse informal semester references ('sem V', 'sem 5', '5th sem', 'fifth sem', 'semester 5') into integer (1..8) & section titles."""
    if not query:
        return entities
    pat = re.compile(
        r"\b(?:sem(?:ester)?\s*([1-8]|i{1,3}|iv|v|vi{0,3}|vii{0,2}|viii|1st|2nd|3rd|[4-8]th|first|second|third|fourth|fifth|sixth|seventh|eighth))\b|"
        r"\b([1-8]|1st|2nd|3rd|[4-8]th|first|second|third|fourth|fifth|sixth|seventh|eighth)\s*sem(?:ester)?\b",
        re.IGNORECASE
    )
    m = pat.search(query)
    if m:
        val = (m.group(1) or m.group(2) or "").lower().strip()
        sem_num = SEMESTER_MAP.get(val)
        if sem_num:
            roman_sem = ROMAN_SEMESTER_MAP.get(sem_num, str(sem_num))
            entities["semester"] = sem_num
            entities["semester_roman"] = roman_sem
            req_sec = entities.setdefault("required_sections", [])
            sec_variants = [f"Semester {roman_sem}", f"Semester {sem_num}", f"Semester {roman_sem} Curriculum"]
            for sec in sec_variants:
                if sec not in req_sec:
                    req_sec.append(sec)
    return entities


def rewrite_personalized_academic_query(query: str, academic_scope=None, identity=None) -> str:
    """Rewrite personalized academic queries ('my program', 'my electives') into explicit program strings using student identity."""
    if not query:
        return query
    q_lower = query.lower()
    
    # Check for personal program references
    personal_prog_triggers = [
        "my program", "my programme", "my branch", "my course", "my curriculum",
        "my credit structure", "my electives", "my degree", "my subjects"
    ]
    
    if any(t in q_lower for t in personal_prog_triggers):
        program_name = None
        if academic_scope and getattr(academic_scope, "programme_id", None):
            program_name = academic_scope.programme_id
        elif identity:
            program_name = (
                getattr(identity, "program", None)
                or getattr(identity, "programme", None)
                or getattr(identity, "dept", None)
                or getattr(identity, "branch", None)
            )

        # Never invent a default programme — that would silently answer MnC/EVD
        # students with ICT curriculum and also bypass academic_scope abstention.
        if not program_name:
            return query

        # Clean program name (e.g. 'B.Tech. (ICT)' -> 'ICT', 'btech-ict' -> 'btech ict')
        prog_clean = (
            program_name.replace("B.Tech.", "")
            .replace("M.Tech.", "")
            .replace("(", "")
            .replace(")", "")
            .replace("-", " ")
            .strip()
            or program_name
        )

        rewritten = query
        for trigger in personal_prog_triggers:
            if trigger in q_lower:
                rewritten = re.sub(
                    re.escape(trigger),
                    f"the {prog_clean} program",
                    rewritten,
                    flags=re.IGNORECASE,
                )
                break
        if "dau" not in rewritten.lower() and "dhirubhai ambani" not in rewritten.lower():
            rewritten += " at Dhirubhai Ambani University (DAU)"
        return rewritten
        
    return query


class QueryPlanner:

    def __init__(self):

        load_dotenv()

        self.model = os.getenv(
            "VLLM_MODEL",
            os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ")
        )

    @staticmethod
    def fallback_plan() -> dict:
        """A neutral plan carrying every key downstream code reads."""
        return {
            "category": "general",
            "intent": "general",
            "confidence": 0.0,
            "retrieval_intent": "general",
            "entity_confidence": 0.5,
            "multi_entity_query": False,
            "query_decomposition": None,
            "entities": {},
            "retrieval_hints": {},
            "top_k": 5,
            "is_claim_verification": False,
            "expanded_terms": [],
            "requires_complete_list": False,
        }

    def plan(self, query, academic_scope=None, identity=None):
        # Follow-ups arrive already rewritten into standalone questions by
        # QueryRewriter, so no continuation handling is needed here.
        effective_query = rewrite_personalized_academic_query(query, academic_scope, identity)
        # Institutional aliases are already appended once by the graph before
        # retrieval; resolving again here would duplicate them.

        scope_hint = ""
        if academic_scope is not None:
            scope_hint = (
                "\nVerified student context (relevance only; never override it): "
                f"programme={academic_scope.programme_id}, "
                f"degree_level={academic_scope.degree_level}, "
                f"admission_year={academic_scope.admission_year}, "
                f"semester={academic_scope.current_semester}.\n"
            )

        def _execute_plan(client):
            return client.chat.completions.create(
                model=self.model,

                temperature=0,

                max_tokens=_PLANNER_MAX_TOKENS,

                response_format={
                    "type": "json_object"
                },

                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": scope_hint + "\nUser query: " + effective_query
                    }
                ],
                extra_body=InferenceRouter.no_think_extra_body(),
            )

        response = InferenceRouter.call_with_rotation(_execute_plan, max_retries=5)

        if not response:
            raise RuntimeError("Failed to generate plan due to API errors.")

        content = (
            (response.choices[0].message.content or "")
            .strip()
        )

        try:
            
            plan = json.loads(content)
            plan.setdefault("entities", {})
            canonicalize_informal_semester(query, plan["entities"])
            # Issue 3 fix: translate informal course names to their exact
            # course_code(s) before retrieval/timetable lookups run.
            resolve_course_name_to_code(query, plan["entities"])
            plan.setdefault("retrieval_hints", {})
            plan.setdefault("top_k", 5)
            plan.setdefault(
                "retrieval_intent",
                "general"
            )
            plan.setdefault(
                "entity_confidence",
                # Fix #14: was 1.0 (maximum), which caused overconfident
                # metadata filters when the LLM omitted this field.
                # 0.5 is a neutral fallback — the pipeline only applies
                # strict filtering when entity_confidence >= 0.85.
                0.5
            )
            plan.setdefault(
                "multi_entity_query",
                False
            )
            plan.setdefault(
                "query_decomposition",
                None
            )
            # Fix QP6: defensive setdefault in case the LLM omits this field
            # despite the schema instruction — keeps retrieval_pipeline.py's
            # plan.get("is_claim_verification") safe without needing a
            # try/except or hardcoded check at the call site.
            plan.setdefault(
                "is_claim_verification",
                False
            )
            # Fix QP7: defensive setdefault for the generic vocabulary
            # expansion field that replaces all topic-specific hardcoded
            # keyword lists previously in aura_chat.py.
            plan.setdefault(
                "expanded_terms",
                []
            )
            # Fix QP8: defensive setdefault for the negation/completeness
            # signal used to widen retrieval top_k generically.
            plan.setdefault(
                "requires_complete_list",
                False
            )

            if plan.get("multi_entity_query"):

                num_entities = 0

                for value in plan.get(
                    "entities",
                    {}
                ).values():

                    if isinstance(value, list):
                        num_entities = max(
                            num_entities,
                            len(value)
                        )

                if num_entities > 1:

                    plan["top_k"] = max(
                        plan.get("top_k", 3),
                        num_entities * 3
                    )

            hints = plan["retrieval_hints"]

            retrieval_intent = plan.get(
                "retrieval_intent",
                "general"
            )

            required_sections = []

            preferred_section_type = None

            if retrieval_intent == "program_eligibility":

                required_sections.extend([
                    "Eligibility",
                    "Eligibility Criteria",
                    "Admissions",
                    "Requirements"
                ])

                preferred_section_type = "eligibility"

            elif retrieval_intent == "faculty_research":

                required_sections.extend([
                    "Research",
                    "Research Interests",
                    "Projects",
                    "Publications"
                ])

                preferred_section_type = "research"

            elif retrieval_intent == "faculty_profile":

                required_sections.extend([
                    "Biography",
                    "Overview",
                    "Research",
                    "Teaching"
                ])

                preferred_section_type = "faculty"

            elif retrieval_intent == "faculty_contact":

                required_sections.extend([
                    "Contact",
                    "Contact Information"
                ])

                preferred_section_type = "contact"

            elif retrieval_intent == "scholarship_information":

                required_sections.extend([
                    "Scholarship",
                    "Financial Assistance",
                    "Fee"
                ])

                preferred_section_type = "scholarship"

            elif retrieval_intent == "admissions_information":

                # Fix Bug3: added "Fee", "Fees Structure", "Tuition" so that
                # fee-related questions classified as admissions_information
                # (e.g. "What is the fee for BS-MS program?") get a reranking
                # boost toward chunks containing fee tables/sections.
                required_sections.extend([
                    "Admissions",
                    "Application Process",
                    "Requirements",
                    "Fee",
                    "Fees Structure",
                    "Tuition"
                ])

                preferred_section_type = (
                    "admissions"
                )

            elif retrieval_intent == "program_curriculum":

                required_sections.extend([
                    "Curriculum",
                    "Courses",
                    "Course Structure"
                ])

                preferred_section_type = (
                    "curriculum"
                )

            elif retrieval_intent == "event_information":

                required_sections.extend([
                    "Event",
                    "Schedule",
                    "Registration",
                    "Details"
                ])

                preferred_section_type = (
                    "event"
                )

            elif retrieval_intent == "policy_version":

                # Fix PV1: policy version/metadata questions (Type4) need
                # "Version History", "Supersedes", and "Effective Date" boosted
                # so the reranker prioritises chunks from the version history
                # section of each policy document.
                required_sections.extend([
                    "Version History",
                    "Supersedes",
                    "Effective Date",
                    "Revision",
                    "Amendment"
                ])

                preferred_section_type = "administration"

            elif retrieval_intent == "rules":

                # Fix QP2: queries about examination rules, malpractice,
                # academic regulations, and code of conduct map to intent
                # "rules" but previously triggered NO required_sections boost.
                # This caused general course policy chunks to outrank actual
                # regulation chunks. Boosting these headers fixes Vedant
                # report failures (95.33% → target 99%+).
                required_sections.extend([
                    "Regulations",
                    "Rules",
                    "Malpractices",
                    "Code of Conduct",
                    "Guidelines",
                    "Academic Policy",
                    "Disciplinary",
                    "Examination Policy"
                ])

                preferred_section_type = "rules"

            elif retrieval_intent == "event_version":

                # Fix QP3: annual event comparison queries (18th vs 19th vs
                # 20th Convocation) need version/chronology section boost so
                # old event schedules don't override current statistics.
                # Addresses Events domain report failures.
                required_sections.extend([
                    "Version History",
                    "Effective Date",
                    "Convocation",
                    "Annual",
                    "Edition",
                    "Schedule"
                ])

                preferred_section_type = "event"

            # Fix QP1: for "general" intent (placement, hostel, campus life,
            # ragging, transport etc.) no required_sections were ever set, so
            # the reranker couldn't boost relevant section headings. Populate
            # them now from the retrieval_hints the LLM already provided (if any),
            # so planner-supplied hints are always honoured.
            if not required_sections and hints.get("required_sections"):
                required_sections = hints["required_sections"]

            hints["preferred_section_type"] = preferred_section_type
            hints["required_sections"] = required_sections

            entities = plan["entities"]
            
            person_name = entities.get("person_name")
            department_name = entities.get("department_name")
            intent = plan.get("intent", "general")
            retrieval_intent = plan.get("retrieval_intent", "general")

            if (
                intent == "eligibility"
                and plan.get("multi_entity_query")
            ):
                decomposition = (
                    plan.get(
                        "query_decomposition"
                    )
                    or []
                )

                decomposition.append(
                    "undergraduate admission eligibility criteria"
                )

                plan["query_decomposition"] = decomposition

            if person_name and not plan.get("multi_entity_query"):
                if retrieval_intent == "faculty_profile":
                    plan["top_k"] = 3

                elif retrieval_intent == "faculty_contact":
                    plan["top_k"] = 2

                elif retrieval_intent == "faculty_research":
                    plan["top_k"] = 3

                else:
                    plan["top_k"] = 3
            
            elif department_name:
                plan["top_k"] = 5

            query_lower = query.lower()

            if (
                query_lower.startswith("who is")
                and not person_name
            ):
                plan["retrieval_hints"].setdefault(
                    "boost_sections",
                    []
                )

                plan["retrieval_hints"]["boost_sections"].extend([
                    "Overview",
                    "Profile",
                    "Biography",
                    "Leadership"
                ])
            
            entity_confidence = plan.get("entity_confidence", 1.0)

            try:
                entity_confidence = float(entity_confidence)
            except:
                entity_confidence = 1.0
            
            plan["entity_confidence"] = max(0.0, min(entity_confidence, 1.0))

            return plan

        except Exception as exc:
            logger.error(
                "query planner returned an unusable plan (%s); using fallback. raw=%r",
                exc, content[:200],
            )
            return self.fallback_plan()
