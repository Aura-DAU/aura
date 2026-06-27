import json
import os
import time

from dotenv import load_dotenv
from pipeline.key_manager import KeyManager


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
- general

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
  "retrieval_hints": {}
}

Every field in the output schema is mandatory.

If a field has no applicable value:

- use an empty object {} for entities and retrieval_hints
- use null for query_decomposition
- use false for booleans
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
"""

class QueryPlanner:

    def __init__(self):

        load_dotenv()

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    def plan(self, query):

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
                        "content": query
                    }
                ]
            )

        response = KeyManager.call_with_rotation(_execute_plan, max_retries=5)

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

                required_sections.extend([
                    "Admissions",
                    "Application Process",
                    "Requirements"
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
                "top_k": 5
            }