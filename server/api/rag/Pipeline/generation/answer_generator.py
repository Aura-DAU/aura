import os
import re
from dotenv import load_dotenv
from groq import Groq


SYSTEM_PROMPT = """
You are AURA, the official AI assistant for Dhirubhai Ambani University (DAU).

You must answer ONLY from the provided university context.

Rules:
- Use only information present in the context.
- Do not invent facts.
- Use conversation history when resolving references such as:
  "he", "she", "they", "it",
  "that faculty member",
  "that program",
  "that event".
- If the answer cannot be determined from the context, say:
  "I could not find that information in the available university data."
- Keep responses clear and professional.
- Combine information from multiple sources when appropriate.
"""

class AnswerGenerator:

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

    def generate(
        self,
        query,
        context,
        history=None
    ):
        
        history_text = ""

        if history:
            for turn in history[-8:]:
                role = turn.get("role")
                content = turn.get("content")
                if role in ["user", "assistant"] and content:
                    if role == "assistant":
                        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                    history_text += (
                        f"{role}: "
                        f"{content}\n"
                    )

        prompt = f"""
Conversation History:
{history_text}

Question:
{query}

Context:
{context}
"""
        try:
            response = (
                self.client.chat.completions.create(
                    model=self.model,

                    temperature=0.2,
                    reasoning_effort="none",

                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
            )

            answer = response.choices[0].message.content

            answer = re.sub(
                r"<think>.*?</think>",
                "",
                answer,
                flags=re.DOTALL
            ).strip()

            # Programmatic Guardrails for Out-of-Scope queries
            out_of_scope_response = "I'm sorry, I can only help with questions about Dhirubhai Ambani University. Is there something else about DAU I can assist you with?"
            
            # Check if the model generated code blocks (which DAU documents never contain)
            if "```" in answer:
                return out_of_scope_response

            # Check for general programming/code requests in the question if the answer is generic code
            question_lower = query.lower()
            programming_keywords = ["write a", "code for", "program for", "how to write", "implement a", "palindrome", "function in", "script in", "python", "c++", "java", "javascript", "html", "css"]
            if any(kw in question_lower for kw in programming_keywords):
                if "DAU" not in answer and "[Source:" not in answer:
                    return out_of_scope_response

            return answer
    
        except Exception as e:
            print(e)
            return "Sorry, I encountered an error while generating a response."