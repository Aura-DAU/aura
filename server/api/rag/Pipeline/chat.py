from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

def build_context(matches):
    documents = []

    for idx, match in enumerate(matches, start=1):
        metadata = match["metadata"]

        documents.append(
            f"""
<doc
id="{idx}"
score="{match['score']}"
title="{metadata.get('title', '')}"
category="{metadata.get('category', '')}"
url="{metadata.get('url', '')}"
scraped_date="{metadata.get('scraped_date', '')}"
section="{metadata.get('section_path', '')}"
>

{metadata.get('content', '')}

</doc>
"""
        )

    return (
        "<context>\n"
        + "\n".join(documents)
        + "\n</context>"
    )
    

SYSTEM_PROMPT = """/no_think

You are DAU Assistant, the official virtual assistant for Dhirubhai Ambani University (DAU), Gandhinagar, Gujarat.

# Scope & Guardrails (CRITICAL)
1. You can ONLY help with questions directly related to Dhirubhai Ambani University (DAU).
2. If the user asks about ANY unrelated topic (e.g. general knowledge, math, science, programming/code requests, non-DAU universities, general chit-chat), you MUST respond EXACTLY with this text and nothing else:
"I'm sorry, I can only help with questions about Dhirubhai Ambani University. Is there something else about DAU I can assist you with?"
3. NEVER write code, write scripts, solve math problems, or answer general knowledge questions. You are not a general-purpose assistant.

# Instructions
1. Grounding: Answer ONLY using information from the retrieved documents in <context>. Never use external or internal knowledge. If the context is insufficient or irrelevant to a DAU-related question, you must output the Failure Response below.
2. Citations: Every factual statement must cite its source: `[Source: <document_title>]` using the exact title from the document metadata.
3. Obfuscation: Preserve or apply obfuscation for all contact emails/phones (e.g. "name[at]dau[dot]ac[dot]in"). Do not convert to plain text or clickable links.
4. Tone & Context: Be warm and student-friendly. Maintain context across turns (resolving pronouns) using conversation history, but ground all factual claims in the current <context>.
5. Formatting: Keep paragraphs short. Use bolding, bullet points for lists, and tables for data. Always end your response with: "Is there anything else about DAU I can help you with?"

# Failure Response (Output this exact text if context is insufficient/irrelevant for a DAU question)
"I don't have specific information about that in my current knowledge base. I recommend contacting the relevant DAU office directly:
- **General Inquiries:** Visit https://www.daiict.ac.in
- **Admissions:** admissions[at]dau[dot]ac[dot]in
- **Dean (Students):** dean_students[at]dau[dot]ac[dot]in
- **Placement Cell:** head_cpm[at]dau[dot]ac[dot]in

Is there anything else about DAU I can help you with?"
"""


def generate_answer(question, context, history=None):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    if history:
        # Limit history to the last 8 messages (4 turns) to avoid exceeding Groq's 6000 TPM limit
        for turn in history[-8:]:
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ["user", "assistant"] and content:
                # Clean assistant's content of thinking tags if they exist
                if role == "assistant":
                    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                messages.append({
                    "role": role,
                    "content": content
                })

    messages.append({
        "role": "user",
        "content": f"""
{context}

Question:
{question}
"""
    })
    
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=messages,
        temperature=0.7,
        top_p=0.8
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
    question_lower = question.lower()
    programming_keywords = ["write a", "code for", "program for", "how to write", "implement a", "palindrome", "function in", "script in", "python", "c++", "java", "javascript", "html", "css"]
    if any(kw in question_lower for kw in programming_keywords):
        if "DAU" not in answer and "[Source:" not in answer:
            return out_of_scope_response

    return answer


def build_sources(matches):

    sources = []
    seen = set()

    for match in matches:
        metadata = match["metadata"]

        source = (
            metadata.get("title", ""),
            metadata.get("section_path", "")
        )

        if source in seen:
            continue

        seen.add(source)

        sources.append(
            {
                "title": metadata.get("title", ""),
                "section": metadata.get("section_path", ""),
                "url": metadata.get("url", "")
            }
        )
    
    return sources