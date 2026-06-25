import os

from dotenv import load_dotenv
from groq import Groq


class QueryRewriter:

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

    def rewrite(
        self,
        query,
        history=None
    ):

        if not history:
            return query
        

        history_text = ""

        for turn in history[-8:]:

            history_text += (
                f"{turn['role']}: "
                f"{turn['content']}\n"
            )

        prompt = f"""
Given the conversation history and the latest user question,
rewrite the latest question so it becomes fully self-contained.

Rules:
- Preserve the original meaning.
- Resolve references such as:
  he, she, him, her, they, them,
  this faculty member,
  this program,
  this event,
  it, its.
- Return ONLY the rewritten question.
- If the question is already self-contained, return it unchanged.

Conversation:

{history_text}

Latest Question:
{query}
"""

        response = (
            self.client.chat.completions.create(
                model=self.model,

                temperature=0,

                # reasoning_effort="none",

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        )

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )