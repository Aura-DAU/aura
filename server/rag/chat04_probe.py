"""CHAT-04 diagnostic probe (temporary; delete after use).

Samples real curriculum phrasings against the live intent classifier via the
same code path production uses (PersonalDataIntentRouter.classify).
"""
import logging
import os
import sys
from collections import Counter

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s %(message)s")

os.environ.setdefault(
    "VLLM_ENDPOINTS",
    "http://10.100.97.71:8001/v1,http://10.100.97.72:8000/v1,http://10.100.97.73:8000/v1",
)
os.environ.setdefault("VLLM_MODEL", "aura-llm")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.ecampus.intent_router import PersonalDataIntentRouter  # noqa: E402

CURRICULUM = [
    "What are the academic requirements for B.Tech ICT?",
    "What is the curriculum for B.Tech ICT?",
    "How many credits do I need to graduate?",
    "What is the course structure for my program?",
    "What are the graduation requirements for BTech ICT?",
    "Show me the syllabus for B.Tech ICT",
    "What courses are in semester 5 of ICT?",
    "How many electives do I need to take?",
    "What is the minimum CPI required to continue in the program?",
    "What are the rules for course load in a regular semester?",
    "What is the credit requirement for the ICT-CS honours program?",
    "Tell me about the B.Tech ICT program structure",
    "What are the academic requirements for M.Tech ICT?",
    "Which courses are compulsory in my branch?",
    "What is the semester 3 curriculum for ICT?",
]
CONTROL_COMMUNITY = [
    "Who is Aditya Tatu?",
    "when is mid-sem",
    "give me timetable of BTech ICT 3rd sem sec A",
    "anti-ragging policy",
    "placement statistics",
]
CONTROL_PERSONAL = ["What is my CGPA?", "show my attendance", "my timetable"]
CONTROL_GENERAL = ["hello", "thanks", "what can you do"]


def run(label, queries, acceptable):
    router = PersonalDataIntentRouter()
    print(f"\n-- {label} (acceptable: {' or '.join(sorted(acceptable))}) --")
    counts, bad = Counter(), []
    for q in queries:
        try:
            verdict = router.classify(q)
        except Exception as exc:
            verdict = f"ERROR:{type(exc).__name__}"
        counts[verdict] += 1
        ok = verdict in acceptable
        if not ok:
            bad.append((q, verdict))
        print(f"  {'ok  ' if ok else 'MISS'} {verdict:14} {q}")
    print(f"  -> {dict(counts)}")
    return counts, bad


if __name__ == "__main__":
    all_bad = []
    c1, b1 = run("CURRICULUM phrasings", CURRICULUM, {"COMMUNITY"})
    all_bad += [("curriculum", q, v) for q, v in b1]
    _, b2 = run("CONTROL community", CONTROL_COMMUNITY, {"COMMUNITY"})
    all_bad += [("control-community", q, v) for q, v in b2]
    _, b3 = run("CONTROL personal", CONTROL_PERSONAL, {"PERSONAL_DATA"})
    all_bad += [("control-personal", q, v) for q, v in b3]
    _, b4 = run("CONTROL general", CONTROL_GENERAL, {"GENERAL"})
    all_bad += [("control-general", q, v) for q, v in b4]

    print("\n===== VERDICT =====")
    print(f"curriculum queries routed GENERAL (CHAT-04 hypothesis): "
          f"{c1.get('GENERAL', 0)}/{len(CURRICULUM)}")
    if all_bad:
        print("All misses:")
        for group, q, v in all_bad:
            print(f"  [{group}] {v:14} {q}")
