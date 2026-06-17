import json
import os
import re
import time

from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError


SYSTEM_PROMPT = """
You are a retrieval planner for a university RAG assistant.

Your job is to analyze the user's query and produce a retrieval plan.

Available categories:
- faculty
- academics
- admissions
- events
- research
- campus_life
- administration
- general

Available intents:
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

Available entity types:
- faculty_name
- event_name
- program_name
- department_name
- scholarship_name
- course_code
- course_name
- semester

Extract entities when present.

Available retrieval intents:
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

Additional fields:

- retrieval_intent
- entity_confidence
- multi_entity_query

Rules:
- entity_confidence must be a float between 0 and 1.
- multi_entity_query should be true when multiple faculty members,
  programs, events, scholarships, or major topics are referenced.
- When multiple entities of the same type are present,
  store them as arrays.
- When a faculty member, program, event, scholarship, or department is mentioned by name, it MUST be extracted into the entities field.

Return ONLY valid JSON.

For eligibility questions:

{
  "category": "admissions",
  "intent": "eligibility",
  "retrieval_intent": "program_eligibility",

  "retrieval_hints": {
    "required_sections": [
      "Eligibility Criteria",
      "Admissions",
      "Requirements"
    ]
  }
}

Example:

Query:
Who is Abhishek Jindal?

{
    "category": "faculty",
    "intent": "overview",
    "retrieval_intent": "faculty_profile",
    "entity_confidence": 0.98,
    "multi_entity_query": false,
    "entities": {
        "faculty_name": "Abhishek Jindal"
    }
}

Query:
What are Abhishek Jindal's research interests?

{
    "category": "faculty",
    "intent": "research",
    "retrieval_intent": "faculty_research",
    "entity_confidence": 0.98,
    "multi_entity_query": false,
    "entities": {
        "faculty_name": "Abhishek Jindal"
    }
}

Query:
Compare BTech CSAI and BTech ICT

{
    "category": "academics",
    "intent": "overview",
    "retrieval_intent": "program_overview",
    "entity_confidence": 0.95,
    "multi_entity_query": true,

    "entities": {
        "program_name": [
            "BTech CSAI",
            "BTech ICT"
        ]
    }
}

Query:
What semester is IT205 offered in?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.99,
  "multi_entity_query": false,
  "entities": {
    "course_code": "IT205"
  }
}

Query:
How many credits does IT205 have?

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.99,
  "multi_entity_query": false,
  "entities": {
    "course_code": "IT205"
  }
}

Query:
List all courses in Semester I for BTech ICT

{
  "category": "academics",
  "intent": "overview",
  "retrieval_intent": "program_curriculum",
  "entity_confidence": 0.98,
  "multi_entity_query": false,
  "entities": {
    "program_name": "BTech ICT",
    "semester": "I"
  }
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
"""


class QueryPlanner:

    def __init__(self):

        load_dotenv()
        from pipeline.key_manager import KeyManager
        self.KeyManager = KeyManager

        self.client = Groq(
            api_key=self.KeyManager.get_current_key()
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3-32b"
        )

    def plan(self, query):

        max_retries = 15
        retry_delay = 5
        response = None
        keys_tried = set()

        attempt = 0
        while attempt < max_retries:
            try:
                # Ensure client is using the current key
                self.client = Groq(api_key=self.KeyManager.get_current_key())
                response = (
                    self.client.chat.completions.create(
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
                )
                break
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                status_code = getattr(e, "status_code", None)
                error_msg = str(e).lower()
                is_daily_limit = "tpd" in error_msg or "tokens per day" in error_msg or "rpd" in error_msg or "requests per day" in error_msg
                
                if is_daily_limit and status_code == 429:
                    current_key = self.KeyManager.get_current_key()
                    keys_tried.add(current_key)
                    if len(keys_tried) >= len(self.KeyManager._keys):
                        print("All API keys exhausted for daily limits in QueryPlanner. Failing request.")
                        raise e
                    
                    print(f"Daily rate limit hit in QueryPlanner: {e}. Rotating API key...")
                    self.KeyManager.rotate_key()
                    # Retry immediately with the new key without incrementing attempt or sleeping
                    continue
                
                is_retryable = (status_code in [429, 500, 502, 503, 504]) or isinstance(e, APIConnectionError)
                if is_retryable:
                    if attempt == max_retries - 1:
                        print("Max retries reached in QueryPlanner. Failing request.")
                        raise e
                    
                    retry_after = retry_delay
                    match = re.search(r"try again in (\d+(?:\.\d+)?)s", str(e))
                    if match:
                        retry_after = float(match.group(1)) + 1.0  # Add 1s buffer
                    
                    # Cap sleep at 65s since Groq token rate limits reset per minute
                    retry_after = min(retry_after, 65.0)
                    
                    print(f"API error/timeout {status_code} in QueryPlanner: {e}. Retrying in {retry_after:.2f} seconds...")
                    time.sleep(retry_after)
                    retry_delay *= 2
                    attempt += 1
                else:
                    raise e
            except Exception as e:
                raise e

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
                1.0
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

                "entities": {},

                "retrieval_hints": {},

                "top_k": 5
            }