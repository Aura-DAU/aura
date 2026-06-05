from Pipeline.retrieve import retrieve
from Pipeline.chat import build_context, generate_answer, build_sources

def answer_question(question: str, history=None, student_profile=None):
    matches = retrieve(question, top_k=3)
    context = build_context(matches)
    answer = generate_answer(question, context, history=history, student_profile=student_profile)
    sources = build_sources(matches)

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }