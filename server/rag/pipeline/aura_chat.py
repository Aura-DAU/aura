#Chat pipeline for AURA RAG system
import os
import re
from pipeline.retrieval.retrieval_pipeline import (
    RetrievalPipeline
)

from pipeline.generation.answer_generator import (
    AnswerGenerator
)

from pipeline.guardrails.query_guardrail import (
    QueryGuardrail
)

def is_greeting_or_meta(query):
    # Fix #7: strip ALL trailing punctuation in one pass instead of chained
    # rstrip calls that only remove one character each.
    q = re.sub(r'[?.!,]+$', '', query.strip()).lower().strip()
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning",
        "good afternoon", "good evening", "how are you", "who are you",
        "who is aura", "what is aura", "what can you do", "help", "menu",
        "intro", "introduce yourself"
    }
    if q in greetings:
        return True
    words = q.split()
    # Allow greeting combos up to 3 words (e.g. "hello aura" or "hey there")
    if len(words) <= 3 and any(w in greetings for w in words):
        return True
    return False


class AuraChat:

    def __init__(self):
        self.pipeline = (
            RetrievalPipeline()
        )
        self.generator = (
            AnswerGenerator()
        )
        self.guardrail = (
            QueryGuardrail()
        )

    def chat(
        self,
        query,
        history=None,
        profile=None
    ):
        try:
            # 1. Semantic Guardrail Evaluation
            if not self.guardrail.is_safe(query):
                return {
                    "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                    "sources": []
                }

            # Guardrail / Query Augmentation for RBAC
            retrieval_query = query
            if profile:
                role = profile.get("role", "student")
                if role == "professor":
                    subjects = profile.get("subjects", [])
                    if subjects:
                        subjects_str = ", ".join(subjects)
                        retrieval_query = f"{query} (Context: student data related to {subjects_str})"

            # Fix Bug5: fee-related queries need "Fees Structure" injected
            # into the retrieval query so BM25 keyword matching can find the
            # right section even when the question is phrased generically
            # (e.g. "what is the fee for BS-MS" → no heading keywords).
            FEE_KEYWORDS = ["fee", "fees", "tuition", "charges", "cost", "payment", "caution deposit"]
            query_lower_check = retrieval_query.lower()
            if any(kw in query_lower_check for kw in FEE_KEYWORDS):
                retrieval_query = retrieval_query + " Fees Structure Tuition"

            retrieval_result = (
                self.pipeline.get_context(
                    retrieval_query,
                    history=history
                )
            )

            # Fix #1B: use the raw Pinecone cosine score (stored as
            # 'cosine_score' by the retriever) for the 0.60 threshold check.
            # Fix AC1: if retrieval returned zero chunks (e.g. Pinecone
            # connection issue or a silent exception in the pipeline), the
            # max() calls below return their defaults, which is correct.
            # However, we also log this so it's visible in DEBUG mode.
            chunks = retrieval_result.get("chunks", [])

            if not chunks and os.getenv("DEBUG", "false").lower() == "true":
                print("[Router] WARNING: retrieval returned 0 chunks for query:", query)

            top_cosine = max(
                [(c.get("cosine_score") or 0.0) for c in chunks],
                default=0.0
            )
            top_cross = max(
                [(c.get("cross_score") or -10.0) for c in chunks],
                default=-10.0
            )

            # Permit simple greetings to pass to RAG
            is_greeting = is_greeting_or_meta(query)
            is_high_confidence = is_greeting or (top_cosine >= 0.45) or (top_cross >= 0.0)  # Fix Bug2: lowered from 0.60

            router_decision = "RAG" if is_high_confidence else "FALLBACK"
            
            # Log query routing details in debug mode
            if os.getenv("DEBUG", "false").lower() == "true":
                print("\n--- DEBUG QUERY ROUTER LOG ---")
                print(f"query: {query}")
                print(f"router_decision: {router_decision}")
                print(f"router_confidence: top_cosine={top_cosine:.4f}, top_cross={top_cross:.4f}")
                print(f"top_k_before_rerank: {retrieval_result.get('top_k_before_rerank', 0)}")
                print(f"top_k_after_rerank: {retrieval_result.get('top_k_after_rerank', 0)}")
                print(f"retrieved_sources: {[c['id'] for c in retrieval_result.get('chunks', [])]}")
                print(f"final_context: {retrieval_result.get('context', '')[:300]}...")
                print("-------------------------------\n")

            if not is_high_confidence:
                return {
                    "answer": "I'm sorry, I can only help with questions about Dhirubhai Ambani University. Is there something else about DAU I can assist you with?",
                    "sources": []
                }

            answer = (
                self.generator.generate(
                    query=retrieval_result.get("corrected_query", query),
                    context=retrieval_result[
                        "context"
                    ],
                    plan=retrieval_result["plan"],
                    history=history,
                    profile=profile
                )
            )

            return {

                "answer": answer,

                "sources":
                    retrieval_result[
                        "sources"
                    ]
            }
        except Exception as e:
            import traceback
            print("Error in AuraChat.chat:", e)
            traceback.print_exc()
            return {
                "answer": "Sorry, I encountered an error while generating a response. Please try again.",
                "sources": []
            }