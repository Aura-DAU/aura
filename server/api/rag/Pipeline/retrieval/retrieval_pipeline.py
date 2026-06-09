from Pipeline.retrieval.query_planner import QueryPlanner
from Pipeline.retrieval.retriever import Retriever
from Pipeline.retrieval.reranker import Reranker
from Pipeline.retrieval.context_builder import ContextBuilder

import re


class RetrievalPipeline:

    def __init__(self):

        self.planner = QueryPlanner()

        self.retriever = Retriever()

        self.reranker = Reranker()

        self.builder = ContextBuilder()

        from Pipeline.retrieval.query_rewriter import QueryRewriter
        self.rewriter = QueryRewriter()

    def _build_metadata_filter(
        self,
        plan
    ):

        entities = plan.get(
            "entities",
            {}
        )

        faculty_name = entities.get(
            "faculty_name"
        )

        if faculty_name:

            return {
                "faculty_name": {
                    "$eq": faculty_name
                }
            }
    
        return None

    def get_context(
        self,
        query,
        history=None
    ):
        
        REFERENCE_WORDS = [
            "he",
            "his",
            "him",
            "she",
            "her",
            "they",
            "their",
            "them",
            "it",
            "its",
            "that faculty",
            "that professor",
            "that event",
            "that program",
            "this program",
            "this event"
        ]

        query_lower = query.lower()
        
        needs_rewrite = any(
            re.search(
                rf"\b{re.escape(ref)}\b",
                query_lower
            )
            for ref in REFERENCE_WORDS
        )

        if needs_rewrite:
            query = (
                self.rewriter.rewrite(
                    query,
                    history
                )
            )

        plan = self.planner.plan(
            query
        )

        entities = plan.get("entities", {})

        event_name = entities.get("event_name")

        program_name = entities.get("program_name")

        if event_name:
            query += " " + event_name

        if isinstance(program_name, str):
            query += " " + program_name

        elif isinstance(program_name, list):
            query += " " + " ".join(program_name)


        metadata_filter = (
            self._build_metadata_filter(
                plan
            )
        )

        final_top_k = plan.get(
            "top_k",
            5
        )

        retrieval_top_k = max(
            final_top_k * 3,
            10
        )
        
        results = (
            self.retriever.retrieve(
                query=query,
                top_k=retrieval_top_k,
                metadata_filter=metadata_filter
            )
        )

        reranked = (
            self.reranker.rerank(
                results,
                plan
            )
        )

        final_chunks = reranked[
            :final_top_k
        ]

        built = (
            self.builder.build(
                final_chunks
            )
        )

        return {

            "query":
                query,

            "plan":
                plan,

            "chunks":
                final_chunks,

            "context":
                built["context"],

            "sources":
                built["sources"]
        }