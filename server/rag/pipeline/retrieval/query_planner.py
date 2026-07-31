import json
import os
import re
import time

from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter


SYSTEM_PROMPT = """
You are the retrieval planner for AURA, the AI assistant for Dhirubhai Ambani University (DAU).

Your task is to analyze the user's query and generate a retrieval plan as a single JSON object.

Return ONLY valid JSON.
Do not include markdown, explanations, or additional text.

------------------------------------------------------------
TASK
------------------------------------------------------------

Determine:

1. category
2. intent
3. retrieval_intent
4. extracted entities
5. entity_confidence
6. whether multiple entities or topics are requested
7. retrieval hints (when applicable)
8. query decomposition (when applicable)
9. is_claim_verification — true if the user is asking you to confirm or deny
   a claim, rumor, or piece of information they heard from someone else, in
   any phrasing or language register (e.g. "I was told X, is that true?",
   "my friend said X", "is it true that X", "someone mentioned X to me").
   This is a semantic judgment, not a fixed list of trigger phrases — apply
   it whenever the query's structure is "verify this claim" regardless of
   the exact wording used.
10. requires_complete_list — true if answering correctly REQUIRES seeing the
    full enumerated set of items (e.g. negation questions like "what is NOT
    a member", "which of these is NOT included"; or "how many total X are
    there"; or comparison-of-a-set questions). When true, the retrieval
    pipeline will fetch more candidates than usual before reranking, since
    a partial list is insufficient to answer a negation or completeness
    question correctly — the model must see every item to correctly
    identify what is missing or excluded.
11. expanded_terms — a short list (max 5) of formal/document terminology
    that DAU's official documents would likely use for the informal or
    colloquial concepts in the query, if they differ from the query's own
    wording. This is a general-purpose translation step, not a fixed
    synonym dictionary: apply your own knowledge of how Indian university
    administrative documents are phrased.
    Examples of the KIND of gap to bridge (do not memorize these as a list —
    reason about the actual query each time):
    - colloquial "who washes clothes in hostel" → formal terms like
      "laundry service", "dhobi", "linen"
    - colloquial "what do I need to bring on day one" → formal terms like
      "room furnishings", "mattress", "bedding", "items not provided"
    - an ambiguous role name like "the head professor in charge of courses"
      → formal designation terms like "Dean of Academic Programs",
      "Board of Studies Chairman"
    If the query already uses formal/document-like terminology, return an
    empty array — do not pad with redundant terms.

------------------------------------------------------------
VALID VALUES
------------------------------------------------------------

Categories

- faculty
- academics
- admissions
- events
- research
- campus_life
- administration
- general

Intents

- overview
- eligibility
- contact
- research
- location
- event_details
- admission_process
- scholarship
- rules
- facilities
- general

Retrieval Intents

- faculty_profile
- faculty_research
- faculty_contact
- program_overview
- program_eligibility
- program_curriculum
- admissions_information
- scholarship_information
- event_information
- policy_version
- general

Use policy_version when the question asks about:
- when a policy was issued or became effective
- whether a policy supersedes or replaces an older one
- whether a newer version of a policy exists
- what changed between versions of a document

Use rules when the question asks about:
- examination regulations, malpractice, or academic dishonesty
- student code of conduct, disciplinary actions, or penalties
- academic progression rules (credit limits, CPI thresholds, DX grades)
- what is or is not allowed under a specific policy

Use event_version when the question asks about:
- comparing annual editions of the same event (e.g. 18th vs 19th Convocation)
- which year's convocation/event data is current
- changes in event format or statistics between editions

Entity Types

- faculty_name
- event_name
- program_name
- department_name
- scholarship_name
- course_code
- course_name
- semester

------------------------------------------------------------
OUTPUT SCHEMA
------------------------------------------------------------

Return exactly one JSON object using this structure.

{
  "category": "...",
  "intent": "...",
  "retrieval_intent": "...",
  "entity_confidence": 0.0,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {},
  "is_claim_verification": false,
  "requires_complete_list": false,
  "expanded_terms": []
}

Every field in the output schema is mandatory.

If a field has no applicable value:

- use an empty object {} for entities and retrieval_hints
- use null for query_decomposition
- use false for booleans (including is_claim_verification)
- use an empty array [] for expanded_terms when the query already uses formal terms
- use "general" for category, intent, and retrieval_intent when appropriate
- use 0.0 for entity_confidence when no entities are extracted

Never omit a field.

------------------------------------------------------------
RULES
------------------------------------------------------------

- entity_confidence must be between 0.0 and 1.0.
- Extract every explicitly mentioned named entity.
- Do not invent entities.
- If multiple entities of the same type are present, return them as arrays.
- If no entities are present, return an empty object.
- If query decomposition is unnecessary, return null.
- If retrieval_hints are unnecessary, return an empty object.
- Do not generate fields outside the schema.
- Output every field exactly once.
- Do not omit fields.
- Course codes (e.g. IT205, CS301, MA101, ICT623) must always be extracted as course_code entities, even if the query does not explicitly use the word "course".

------------------------------------------------------------
SPECIAL CASES
------------------------------------------------------------

Eligibility questions

Use:

"category": "admissions"

"intent": "eligibility"

"retrieval_intent": "program_eligibility"

and include

"retrieval_hints": {
    "required_sections": [
        "Eligibility Criteria",
        "Admissions",
        "Requirements"
    ]
}

Faculty profile

Example

Query

Who is Abhishek Jindal?

Output

{
  "category":"faculty",
  "intent":"overview",
  "retrieval_intent":"faculty_profile",
  "entity_confidence":0.98,
  "multi_entity_query":false,
  "entities":{
    "faculty_name":"Abhishek Jindal"
  },
  "query_decomposition":null,
  "retrieval_hints":{}
}

Faculty research

Query

What are Abhishek Jindal's research interests?

Output

{
  "category":"faculty",
  "intent":"research",
  "retrieval_intent":"faculty_research",
  "entity_confidence":0.98,
  "multi_entity_query":false,
  "entities":{
    "faculty_name":"Abhishek Jindal"
  },
  "query_decomposition":null,
  "retrieval_hints":{}
}

Multiple programs

Query

Compare BTech CSAI and BTech ICT

Output

{
  "category":"academics",
  "intent":"overview",
  "retrieval_intent":"program_overview",
  "entity_confidence":0.95,
  "multi_entity_query":true,
  "entities":{
    "program_name":[
      "BTech CSAI",
      "BTech ICT"
    ]
  },
  "query_decomposition":[
    "BTech CSAI overview",
    "BTech ICT overview"
  ],
  "retrieval_hints":{}
}

Course lookup

Query

What semester is IT205 offered in?

Output

{
  "category":"academics",
  "intent":"overview",
  "retrieval_intent":"program_curriculum",
  "entity_confidence":0.99,
  "multi_entity_query":false,
  "entities":{
    "course_code":"IT205"
  },
  "query_decomposition":null,
  "retrieval_hints":{}
}

Semester query

Query

List all courses in Semester I for BTech ICT

Output

{
  "category":"academics",
  "intent":"overview",
  "retrieval_intent":"program_curriculum",
  "entity_confidence":0.98,
  "multi_entity_query":false,
  "entities":{
    "program_name":"BTech ICT",
    "semester":"I"
  },
  "query_decomposition":null,
  "retrieval_hints":{}
}

query_decomposition:
- null for normal queries.
- For multi-entity or multi-topic queries,
  provide a list of focused retrieval queries.

Examples:

Query:
Compare BTech CSAI and BTech ICT

query_decomposition:
[
  "BTech CSAI overview",
  "BTech ICT overview"
]

Query:
Tell me about Abhishek Jindal and Arpit Rana

query_decomposition:
[
  "Abhishek Jindal profile",
  "Arpit Rana profile"
]

Query:
Hostel policy and scholarships

query_decomposition:
[
  "Hostel policy",
  "Scholarships available"
]

Fix B — additional few-shot examples for previously uncovered query patterns:

Query:
What courses are offered in Semester 3 and Semester 4 of BTech ICT?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.97,
  "multi_entity_query": true,
  "entities": {
    "program_name": "BTech ICT",
    "semester": ["III", "IV"]
  },
  "query_decomposition": [
    "BTech ICT Semester III courses",
    "BTech ICT Semester IV courses"
  ]
}

Query:
What does the ICT department offer?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_overview",
  "entity_confidence": 0.90,
  "multi_entity_query": false,
  "entities": {
    "department_name": "ICT"
  }
}

Query:
Am I eligible for the merit scholarship with a 9 CGPA?

{
  "category": "admissions",
  "intent": "eligibility",
  "retrieval_intent": "scholarship_information",
  "entity_confidence": 0.92,
  "multi_entity_query": false,
  "entities": {
    "scholarship_name": "merit scholarship"
  },
  "retrieval_hints": {
    "required_sections": ["Eligibility", "Scholarship", "CGPA"]
  }
}

Query:
What is the total fee for BTech ICT?

{
  "category": "admissions",
  "intent": "overview",
  "retrieval_intent": "admissions_information",
  "entity_confidence": 0.93,
  "multi_entity_query": false,
  "entities": {
    "program_name": "BTech ICT"
  },
  "retrieval_hints": {
    "required_sections": ["Fee", "Tuition", "Fees Structure"]
  }
}

Query:
What are Dr. Sourish Dasgupta's research areas?

{
  "category": "faculty",
  "intent": "research",
  "retrieval_intent": "faculty_research",
  "entity_confidence": 0.98,
  "multi_entity_query": false,
  "entities": {
    "faculty_name": "Sourish Dasgupta"
  }
}

Query:
What placement support does DAU provide?

{
  "category": "campus_life",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.80,
  "multi_entity_query": false,
  "entities": {},
  "retrieval_hints": {
    "required_sections": ["Placement", "Career", "Internship"]
  }
}

Query:
Which courses do not count as elective credits in BTech ICT?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.92,
  "multi_entity_query": false,
  "entities": {
    "program_name": "BTech ICT"
  },
  "retrieval_hints": {
    "required_sections": ["Elective", "Credits", "Curriculum"]
  }
}

Query:
What is the fee for BS-MS program?

{
  "category": "admissions",
  "intent": "overview",
  "retrieval_intent": "admissions_information",
  "entity_confidence": 0.93,
  "multi_entity_query": false,
  "entities": {
    "program_name": "BS-MS"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Fee", "Fees Structure", "Tuition", "Admissions"]
  }
}

Query:
How much is the tuition fee at DAU?

{
  "category": "admissions",
  "intent": "overview",
  "retrieval_intent": "admissions_information",
  "entity_confidence": 0.80,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Fee", "Fees Structure", "Tuition"]
  }
}

Query:
What are the hostel charges?

{
  "category": "campus_life",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.80,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Hostel", "Fee", "Charges"]
  }
}

------------------------------------------------------------
COMPARISON QUERIES — always decompose into two focused sub-queries
------------------------------------------------------------

Query:
How does the library borrowing limit for a postgraduate student differ from an undergraduate student?

{
  "category": "campus_life",
  "intent": "general",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "library borrowing limit postgraduate PG student books items loan period",
    "library borrowing limit undergraduate UG BTech student books loan period"
  ],
  "retrieval_hints": {
    "required_sections": ["Borrowing", "Loan Period", "Library", "Resource Centre"]
  }
}

Query:
Between a BTech student and a PhD student, who has a longer borrowing period for library books?

{
  "category": "campus_life",
  "intent": "general",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "library loan period borrowing duration BTech undergraduate student",
    "library loan period borrowing duration PhD doctoral student"
  ],
  "retrieval_hints": {
    "required_sections": ["Borrowing", "Loan Period", "Library"]
  }
}

Query:
How does the refund percentage differ between withdrawing on day 10 versus day 20 after commencement of classes?

{
  "category": "admissions",
  "intent": "overview",
  "retrieval_intent": "admissions_information",
  "entity_confidence": 0.88,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "tuition fee refund percentage withdrawal within 15 days commencement",
    "tuition fee refund percentage withdrawal 16 to 30 days commencement"
  ],
  "retrieval_hints": {
    "required_sections": ["Refund", "Withdrawal", "Fee Refund", "Tuition"]
  }
}

Query:
How does the procedure for student grievances differ from the procedure for faculty grievances under the GRHS?

{
  "category": "administration",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.87,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "student grievance redressal procedure GRHS level authority",
    "faculty grievance redressal procedure GRHS level authority"
  ],
  "retrieval_hints": {
    "required_sections": ["Grievance", "Grievance Redressal", "Procedure", "GRHS"]
  }
}

Query:
Under the patent policy, how does the revenue share differ if the filing cost was covered by a sponsored research funder versus by DAU directly?

{
  "category": "research",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.88,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "patent revenue share distribution DAU funds filing cost",
    "patent revenue share distribution sponsored research project funds filing"
  ],
  "retrieval_hints": {
    "required_sections": ["Patent", "Revenue", "Filing", "Revenue Share"]
  }
}

Query:
Under the hostel allotment policy, are day scholars given hostel rooms on the same basis as outstation students?

{
  "category": "campus_life",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "hostel allotment eligibility day scholar local student",
    "hostel allotment eligibility outstation student priority criteria"
  ],
  "retrieval_hints": {
    "required_sections": ["Hostel", "Allotment", "Eligibility", "Day Scholar"]
  }
}

------------------------------------------------------------
CROSS-POLICY SCENARIO QUERIES — multi-policy decomposition
------------------------------------------------------------

Query:
Does a DX grade make a student ineligible for a merit scholarship?

{
  "category": "academics",
  "intent": "eligibility",
  "retrieval_intent": "scholarship_information",
  "entity_confidence": 0.87,
  "multi_entity_query": true,
  "entities": {
    "scholarship_name": "merit scholarship"
  },
  "query_decomposition": [
    "DX grade attendance penalty academic backlog definition",
    "merit scholarship eligibility criteria backlog academic standing"
  ],
  "retrieval_hints": {
    "required_sections": ["DX", "Scholarship", "Eligibility", "Backlog", "Attendance"]
  }
}

Query:
Can a student who received a disciplinary warning still be allotted a hostel room for the next year?

{
  "category": "campus_life",
  "intent": "eligibility",
  "retrieval_intent": "general",
  "entity_confidence": 0.86,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "hostel allotment eligibility disciplinary action warning suspension",
    "disciplinary warning penalty consequences student hostel"
  ],
  "retrieval_hints": {
    "required_sections": ["Hostel", "Allotment", "Disciplinary", "Warning"]
  }
}

Query:
If a student is on disciplinary probation, are they eligible for the Student Research Excellence Award?

{
  "category": "academics",
  "intent": "eligibility",
  "retrieval_intent": "general",
  "entity_confidence": 0.87,
  "multi_entity_query": true,
  "entities": {},
  "query_decomposition": [
    "Student Research Excellence Award eligibility criteria disciplinary probation",
    "disciplinary probation student standing academic record"
  ],
  "retrieval_hints": {
    "required_sections": ["Research Excellence Award", "Eligibility", "Disciplinary", "Probation"]
  }
}

------------------------------------------------------------
POLICY VERSION / METADATA QUERIES — use effective_date and version_history sections
------------------------------------------------------------

Query:
The PhD Student Travel and Research Allowance Policy has an effective date of 1 January 2026. Does it explicitly mention what earlier policy it supersedes?

{
  "category": "administration",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.82,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Version History", "Supersedes", "Effective Date", "PhD Travel", "Research Allowance"]
  }
}

Query:
The Patent Filing Policy has an effective date of 1 December 2025. Is there any mention of a prior patent policy at DAU?

{
  "category": "research",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.82,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Version History", "Supersedes", "Effective Date", "Patent"]
  }
}

Query:
The Anti-Ragging Committee document for 2025-26 is dated 18 August 2025. Does the same document still apply, or has a newer version been issued?

{
  "category": "administration",
  "intent": "overview",
  "retrieval_intent": "general",
  "entity_confidence": 0.82,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Version History", "Effective Date", "Anti-Ragging", "Ragging Committee"]
  }
}

------------------------------------------------------------
MYTH-BUSTING / CLAIM VERIFICATION (Type9) — always use "rules" intent
------------------------------------------------------------

Query:
A friend told me attendance is tracked overall not per course — is that true?

{
  "category": "academics",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Attendance", "DX", "Academic Policy"]
  },
  "is_claim_verification": true
}

Query:
Someone said alumni data at DAU is shared with placement companies by default — does the alumni data privacy policy permit this?

{
  "category": "administration",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Alumni", "Data Privacy", "Sharing", "Third Party"]
  },
  "is_claim_verification": true
}

Query:
I heard that the Dean of Faculty and the Dean of Academic Programs are the same person at DAU — is that right?

{
  "category": "faculty",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": true,
  "entities": {
    "department_name": ["Dean of Faculty Affairs", "Dean of Academic Programs"]
  },
  "query_decomposition": [
    "Dean of Faculty Affairs name role DAU",
    "Dean of Academic Programs name role DAU Board of Studies Chairman"
  ],
  "retrieval_hints": {
    "required_sections": ["Dean of Faculty", "Dean of Academic Programs", "Board of Studies"]
  },
  "is_claim_verification": true
}

Query:
I was told there are no non-teaching staff at DA-IICT with engineering degrees — is that correct?

{
  "category": "faculty",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.80,
  "multi_entity_query": false,
  "entities": {},
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Non-Teaching Staff", "Engineering", "Qualifications"]
  },
  "is_claim_verification": true,
  "requires_complete_list": true
}

------------------------------------------------------------
NEGATION / ENUMERATION QUERIES — requires_complete_list example
------------------------------------------------------------

Query:
Which of the following is NOT a member of the Board of Studies at DAU: Dean of Research, Dean of Faculty, Director General, Dean of Academic Programs?

{
  "category": "faculty",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.88,
  "multi_entity_query": false,
  "entities": {
    "department_name": "Board of Studies"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Board of Studies", "Members", "Composition", "Chairman"]
  },
  "is_claim_verification": false,
  "requires_complete_list": true
}

Query:
The Board of Studies at DAU does NOT serve which function: curriculum oversight, faculty appointment decisions, academic program governance, or program committee membership?

{
  "category": "faculty",
  "intent": "rules",
  "retrieval_intent": "general",
  "entity_confidence": 0.85,
  "multi_entity_query": false,
  "entities": {
    "department_name": "Board of Studies"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Board of Studies", "Functions", "Responsibilities"]
  },
  "is_claim_verification": false,
  "requires_complete_list": true
}

------------------------------------------------------------
TEMPORAL YEAR ANCHOR — CRITICAL (Fix QP5)
------------------------------------------------------------

If the question explicitly names a specific academic year or rule version
(e.g. "under the 2024-25 rules", "per the 2019-20 regulations", "in the
2022-23 M.Tech ICT curriculum"), include a "rule_year" field in entities:

Query:
Under the 2024-25 PhD rules, what is the maximum credit limit per semester?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "rules",
  "entity_confidence": 0.92,
  "multi_entity_query": false,
  "entities": {
    "program_name": "Ph.D.",
    "rule_year": "2024-25"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Credits", "Maximum", "Academic Requirements"]
  }
}

Query:
What was the minimum credit load for PhD students prior to the 2024-25 rules?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "rules",
  "entity_confidence": 0.90,
  "multi_entity_query": false,
  "entities": {
    "program_name": "Ph.D.",
    "rule_year": "2019-20"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Credits", "Minimum", "Academic Requirements"]
  }
}

Query:
How many core courses are in the first semester of M.Tech EC (2022-23)?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.93,
  "multi_entity_query": false,
  "entities": {
    "program_name": "M.Tech. (EC)",
    "rule_year": "2022-23"
  },
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Core Courses", "Semester I", "Curriculum"]
If no specific year is mentioned in the question, omit "rule_year" entirely.
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


class QueryPlanner:

    def __init__(self):

        load_dotenv()

        self.model = os.getenv(
            "VLLM_MODEL",
            os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ")
        )

    def plan(self, query, academic_scope=None):

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
                        "content": scope_hint + "\nUser query: " + query
                    }
                ],
                extra_body=InferenceRouter.no_think_extra_body(),
            )

        response = InferenceRouter.call_with_rotation(_execute_plan, max_retries=5)

        if not response:
            raise RuntimeError("Failed to generate plan due to API errors.")

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        try:
            
            plan = json.loads(content)
            plan.setdefault("entities", {})
            canonicalize_informal_semester(query, plan["entities"])
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
            
            faculty_name = entities.get("faculty_name")
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

            if faculty_name and not plan.get("multi_entity_query"):
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
                and not faculty_name
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

        except Exception:

            return {
                "category": "general",
                "intent": "general",
                "confidence": 0.0,
                # Fix J: add all keys that downstream code reads so that the
                # fallback plan is a fully-valid plan dict, not a partial one.
                "retrieval_intent": "general",
                "entity_confidence": 0.5,
                "multi_entity_query": False,
                "query_decomposition": None,
                "entities": {},
                "retrieval_hints": {},
                "top_k": 5,
                # Fix QP6: include is_claim_verification in the fallback dict
                # so retrieval_pipeline.py's plan.get("is_claim_verification")
                # never raises on a planner exception — defaults to False,
                # meaning myth-bust augmentation is simply skipped rather than
                # crashing the request.
                "is_claim_verification": False,
                # Fix QP7: same defensive default for expanded_terms.
                "expanded_terms": [],
                # Fix QP8: same defensive default for requires_complete_list.
                "requires_complete_list": False
            }
