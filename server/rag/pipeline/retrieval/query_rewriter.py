import os
from dotenv import load_dotenv
from pipeline.key_manager import KeyManager

class QueryRewriter:

    def __init__(self):
        load_dotenv()
        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
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

        def _execute_rewrite(client):
            return client.chat.completions.create(
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

        response = KeyManager.call_with_rotation(_execute_rewrite, max_retries=5)

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )