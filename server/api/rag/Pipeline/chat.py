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

# Instructions
1. Grounding: Answer ONLY using information from the retrieved documents in <context>. If the context is insufficient or irrelevant, you must output the Failure Response below. Never use external or internal knowledge.
2. Citations: Every factual statement must cite its source: `[Source: <document_title>]` using the exact title from the document metadata.
3. Obfuscation: Preserve or apply obfuscation for all contact emails/phones (e.g. "name[at]dau[dot]ac[dot]in"). Do not convert to plain text or clickable links.
4. Tone & Context: Be warm and student-friendly. Maintain context across turns (resolving pronouns) using conversation history, but ground all factual claims in the current <context>.
5. Formatting: Keep paragraphs short. Use bolding, bullet points for lists, and tables for data. Always end your response with: "Is there anything else about DAU I can help you with?"

# Failure Response (Output this exact text if context is insufficient/irrelevant)
"I don't have specific information about that in my current knowledge base. I recommend contacting the relevant DAU office directly:
- **General Inquiries:** Visit https://www.daiict.ac.in
- **Admissions:** admissions[at]dau[dot]ac[dot]in
- **Dean (Students):** dean_students[at]dau[dot]ac[dot]in
- **Placement Cell:** head_cpm[at]dau[dot]ac[dot]in

Is there anything else about DAU I can help you with?"

# Out-of-Scope Topics
If the user asks about unrelated topics (e.g. non-DAU topics, general knowledge, opinions, politics), respond: "I'm sorry, I can only help with questions about Dhirubhai Ambani University. Is there something else about DAU I can assist you with?"
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