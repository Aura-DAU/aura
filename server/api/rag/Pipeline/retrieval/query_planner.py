import json
import os

from dotenv import load_dotenv
from groq import Groq


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

Extract entities when present.

Return ONLY valid JSON.

Example:

{
    "category": "faculty",
    "intent": "research",
    "confidence": 0.95,

    "entities": {
        "faculty_name": "Abhishek Jindal"
    },

    "retrieval_hints": {
        "boost_sections": [
            "Research",
            "Specialization"
        ]
    },

    "top_k": 3
}
"""


class QueryPlanner:

    def __init__(self):

        load_dotenv()

        self.client = Groq(
            api_key=os.getenv(
                "GROQ_API_KEY"
            )
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3-32b"
        )

    def plan(self, query):

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

            entities = plan["entities"]
            
            faculty_name = entities.get("faculty_name")
            department_name = entities.get("department_name")
            intent = plan.get("intent", "general")

            if faculty_name:
                if intent == "overview":
                    plan["top_k"] = 1
                elif intent == "contact":
                    plan["top_k"] = 2
                elif intent == "research":
                    plan["top_k"] = 3
                else:
                    plan["top_k"] = 3
            
            elif department_name:
                plan["top_k"] = 5

            query_lower = query.lower()
            if query_lower.startswith("who is") and not faculty_name:
                plan["intent"] = "overview"
                plan["retrieval_hints"] = {
                    "boost_sections": [
                        "Overview",
                        "Profile",
                        "Biography",
                        "Leadership"
                    ]
                }

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