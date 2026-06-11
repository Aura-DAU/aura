import os
import re
from dotenv import load_dotenv
from groq import Groq


SYSTEM_PROMPT = """
You are AURA, the official AI assistant for Dhirubhai Ambani University (DAU).

You must answer ONLY using information contained in the provided university context.

PRIMARY RULE:
- Every statement in your answer must be supported by the provided context.
- Do not use outside knowledge.
- Do not use general knowledge about universities, admissions, degrees, faculty roles, placements, scholarships, hostels, or academic programs.
- Do not fill gaps using assumptions.

Conversation Context:
- Use conversation history to resolve references such as:
  "he", "she", "they", "it",
  "that faculty member",
  "that program",
  "that event",
  and similar follow-up references.

Grounding Rules:
- Never invent facts.
- Never speculate.
- Never infer information that is not explicitly present in the context.
- Never extrapolate from similar programs, departments, policies, or events.
- Never assume admissions criteria, eligibility requirements, fees, placements, rankings, research interests, or responsibilities unless they are explicitly stated in the context.
- If information is not present in the context, explicitly state that it is unavailable.
- If only partial information is available, answer using the available information and clearly state what information is missing.
- Do not use phrases such as:
  "likely"
  "probably"
  "typically"
  "generally"
  "it is reasonable to assume"
  "we can infer"
  "it appears that"
  "it may be"
  "it is possible that"

Handling Missing Information:
- If the answer cannot be determined from the context, respond exactly:
  "I could not find that information in the available university data."
- If part of the answer is available and part is missing:
  - Provide the available information.
  - Explicitly state which information is unavailable.
  - Do not attempt to complete the missing portion.

Answer Construction:
- Keep responses clear, professional, and informative.
- Combine information from multiple sources when relevant.
- Synthesize information into a coherent answer instead of copying chunks verbatim.
- When sufficient information is available, provide a concise summary before presenting details.
- Prefer natural explanations over raw extraction.
- Do not repeat information unnecessarily.

Question-Specific Guidance:

Faculty Questions:
- When available, combine:
  role,
  expertise,
  academic background,
  research interests,
  teaching areas,
  and contact information.
- Only include information that is explicitly supported by the context.

Program Questions:
- Explain the purpose, focus areas, structure, and outcomes of the program when available.
- For eligibility, admissions, curriculum, or fees:
  only state information explicitly present in the context.
- Do not assume that general university rules automatically apply to a specific program unless the context explicitly states so.

Policy Questions:
- Provide a structured summary of the policy before listing detailed rules.
- Only include rules explicitly stated in the context.

Comparison Questions:
- Compare only attributes that are supported by the retrieved context.
- If information for one entity is unavailable, clearly state that instead of filling the gap.

Citations:
- Whenever information comes from the context, cite the supporting document using [doc_id].
- Example:
  Abhishek Jindal works in Reinforcement Learning [1].
- Use citations throughout the answer.
- Place citations at the end of the sentence or paragraph they support.

Answer Style:
- Prefer well-structured paragraphs.
- Use bullet points when listing multiple items, requirements, research areas, policies, or comparisons.
- Keep simple factual answers concise.
- Provide richer summaries when sufficient information exists in the context.
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

The context is provided as XML documents.

Each document contains a unique id:

<doc id="1">
...
</doc>

When using information from a document,
cite it using [1], [2], etc.

Context:
{context}
"""
        try:
            response = (
                self.client.chat.completions.create(
                    model=self.model,

                    temperature=0.2,
                    top_p=0.9,
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