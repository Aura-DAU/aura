from pipeline.retrieval.query_planner import QueryPlanner
from pipeline.retrieval.retriever import Retriever
from pipeline.retrieval.reranker import Reranker
from pipeline.retrieval.context_builder import ContextBuilder

import re


class RetrievalPipeline:

    def __init__(self):

        self.planner = QueryPlanner()

        self.retriever = Retriever()

        self.reranker = Reranker()

        self.builder = ContextBuilder()

        from pipeline.retrieval.query_rewriter import QueryRewriter
        self.rewriter = QueryRewriter()

    def _build_metadata_filter(
        self,
        plan
    ):

        def first_value(value):

            if isinstance(value, list):
                return value[0] if value else None

            return value

        entities = plan.get(
            "entities",
            {}
        )

        course_code = first_value(
            entities.get(
                "course_code"
            )
        )

        if course_code:

            return {
                "course_code": {
                    "$eq": course_code
                }
            }

        faculty_name = first_value(
            entities.get(
                "faculty_name"
            )
        )

        if faculty_name:

            return {
                "faculty_name": {
                    "$eq": faculty_name
                }
            }

        event_name = first_value(
            entities.get(
                "event_name"
            )
        )

        if event_name:

            return {
                "event_name": {
                    "$eq": event_name
                }
            }

        program_name = first_value(
            entities.get(
                "program_name"
            )
        )

        semester = first_value(
            entities.get(
                "semester"
            )
        )

        if program_name and semester:

            return {
                "$and": [
                    {
                        "program_name": {
                            "$eq": program_name
                        }
                    },
                    {
                        "semester": {
                            "$eq": semester
                        }
                    }
                ]
            }

        if program_name:

            return {
                "program_name": {
                    "$eq": program_name
                }
            }

        return None
    

    def _normalize_program_name(self, name):
        if not name:
            return ""
            
        name = name.lower()

        name = re.sub(
            r"[^a-z0-9 ]",
            " ",
            name
        )

        name = re.sub(
            r"\s+",
            " ",
            name
        ).strip()

        name = name.replace(
            "b tech",
            "btech"
        )

        name = name.replace(
            "m tech",
            "mtech"
        )

        name = name.replace(
            "m des",
            "mdes"
        )

        name = name.replace(
            "m sc",
            "msc"
        )

        return name


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

        # Rewriting only makes sense mid-conversation. Beyond explicit
        # pronouns, short or "what about..." follow-ups are usually
        # context-dependent too; the rewriter returns self-contained
        # queries unchanged, so over-triggering only costs one LLM call.
        needs_rewrite = bool(history) and (
            any(
                re.search(
                    rf"\b{re.escape(ref)}\b",
                    query_lower
                )
                for ref in REFERENCE_WORDS
            )
            or query_lower.startswith(("what about", "how about", "and ", "also "))
            or len(query.split()) <= 4
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

        if isinstance(event_name, str):
            query += " " + event_name

        elif isinstance(event_name, list):
            query += " " + " ".join(str(e) for e in event_name)

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
        
        decomposed_queries = plan.get(
            "query_decomposition"
        )

        if decomposed_queries:

            all_results = []

            for subquery in decomposed_queries:

                sub_results = (
                    self.retriever.retrieve(
                        query=subquery,
                        top_k=retrieval_top_k,
                        metadata_filter=None
                    )
                )

                sub_reranked = (
                    self.reranker.rerank(
                        query=subquery,
                        results=sub_results,
                        plan=plan
                    )
                )

                all_results.extend(
                    sub_reranked[:3]
                )

            results = all_results
        
        else:
            results = (
                self.retriever.retrieve(
                    query=query,
                    top_k=retrieval_top_k,
                    metadata_filter=metadata_filter
                )
            )

            if not results and metadata_filter:
                print(
                    "Metadata filter returned 0 results. "
                    "Falling back to semantic search."
                )

                results = (
                    self.retriever.retrieve(
                        query=query,
                        top_k=retrieval_top_k,
                        metadata_filter=None
                    )
                )

        seen = set()
        deduped = []

        for result in results:

            chunk_id = result["id"]

            if chunk_id not in seen:

                deduped.append(
                    result
                )

                seen.add(
                    chunk_id
                )

        results = deduped

        if decomposed_queries:

            reranked = results

        else:
            reranked = (
                self.reranker.rerank(
                    query=query,
                    results=results,
                    plan=plan
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
                built["sources"],

            "top_k_before_rerank":
                len(results),

            "top_k_after_rerank":
                len(final_chunks)
        }