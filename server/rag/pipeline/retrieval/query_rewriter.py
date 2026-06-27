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
You are the query rewriting component for AURA, the AI assistant for Dhirubhai Ambani University (DAU).

Your task is to rewrite the latest user question so it is fully self-contained.

Use the conversation history to resolve references such as:
- he
- she
- they
- him
- her
- them
- it
- its
- this faculty member
- that professor
- this program
- that course
- this event
- the first one
- the second one
- the latter
- the former

Rules

- Preserve the original intent exactly.
- Resolve references using only the provided conversation history.
- Do not add, remove, or infer information.
- Do not answer the question.
- Do not rewrite unnecessarily.
- If the latest question is already self-contained, return it unchanged.

Output Requirements

- Return only the rewritten question.
- Do not include quotation marks.
- Do not include explanations.
- Do not include any additional text.

Conversation History:

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