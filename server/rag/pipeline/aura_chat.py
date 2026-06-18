#Chat pipeline for AURA RAG system
import os
from pipeline.retrieval.retrieval_pipeline import (
    RetrievalPipeline
)

from pipeline.generation.answer_generator import (
    AnswerGenerator
)


def is_greeting_or_meta(query):
    q = query.strip().lower().rstrip("?").rstrip("!").rstrip(".")
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning", 
        "good afternoon", "good evening", "how are you", "who are you", 
        "who is aura", "what is aura", "what can you do", "help", "menu",
        "intro", "introduce yourself"
    }
    if q in greetings:
        return True
    words = q.split()
    if len(words) <= 2 and any(w in greetings for w in words):
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

    def chat(
        self,
        query,
        history=None,
        profile=None
    ):
        retrieval_result = (
            self.pipeline.get_context(
                query,
                history=history
            )
        )

        # Retrieval confidence decides
        top_score = retrieval_result["chunks"][0].get("score", 0.0) if retrieval_result["chunks"] else 0.0
        
        # Permit simple greetings to pass to RAG
        is_greeting = is_greeting_or_meta(query)
        is_high_confidence = is_greeting or (top_score >= 0.60)
        
        router_decision = "RAG" if is_high_confidence else "FALLBACK"
        
        # Log query routing details in debug mode
        if os.getenv("DEBUG", "false").lower() == "true":
            print("\n--- DEBUG QUERY ROUTER LOG ---")
            print(f"query: {query}")
            print(f"router_decision: {router_decision}")
            print(f"router_confidence: {top_score:.4f}")
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