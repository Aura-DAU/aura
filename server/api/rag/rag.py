from Pipeline.retrieve import retrieve
from Pipeline.chat import build_context, generate_answer, build_sources

def answer_question(question: str):
    matches = retrieve(question, top_k=20)
    context = build_context(matches)
    answer = generate_answer(question, context)
    sources = build_sources(matches)

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }