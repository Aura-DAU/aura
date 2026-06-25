from pipeline.retrieval.query_planner import QueryPlanner
from pipeline.retrieval.retriever import Retriever
from pipeline.retrieval.reranker import Reranker
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.retrieval.entity_retriever import EntityRetriever

import re
import logging

logger = logging.getLogger(__name__)

class RetrievalPipeline:

    def __init__(self):

        self.planner = QueryPlanner()

        self.retriever = Retriever()

        self.reranker = Reranker()

        self.builder = ContextBuilder()

        from pipeline.retrieval.query_rewriter import QueryRewriter
        self.rewriter = QueryRewriter()

        # Shared: load metadata.json once for both faculty fuzzy-matching
        # and entity-based retrieval (professor's algorithm).
        import json
        from pathlib import Path
        metadata_path = (
            Path(__file__).resolve().parent.parent
            / "vector_store"
            / "metadata.json"
        )

        # ── Faculty fuzzy matching ────────────────────────────────────────
        self.faculty_names = []
        self.faculty_names_lower = []
        self.faculty_names_map = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                self.faculty_names = sorted(list({
                    chunk["faculty_name"]
                    for chunk in chunks
                    if chunk.get("faculty_name")
                }))
                self.faculty_names_lower = [n.lower() for n in self.faculty_names]
                self.faculty_names_map = {n.lower(): n for n in self.faculty_names}
                logger.info("Loaded %d unique faculty names for fuzzy matching.", len(self.faculty_names))
            except Exception as e:
                logger.warning("Failed to load faculty names from metadata.json: %s", e)
        else:
            logger.warning("metadata.json not found at %s. Fuzzy faculty matching disabled.", metadata_path)

        # ── Entity-based retrieval (professor's algorithm) ─────────────────
        # Chunks → Triples → Entity → Chunk Pool
        # Loads entity_index.json built by build_entity_index.py.
        # Gracefully disabled if the index or metadata file is absent.
        if metadata_path.exists():
            try:
                self.entity_retriever = EntityRetriever(
                    str(metadata_path)
                )
                logger.info("EntityRetriever initialised successfully.")
            except Exception as e:
                logger.warning(
                    "EntityRetriever failed to initialise: %s. "
                    "Entity-based retrieval disabled.",
                    e,
                )
                self.entity_retriever = None
        else:
            logger.warning(
                "metadata.json not found — EntityRetriever disabled."
            )
            self.entity_retriever = None

    PROGRAM_ALIASES = {

        "ict": "B.Tech. (ICT)",
        "btech ict": "B.Tech. (ICT)",
        "b.tech ict": "B.Tech. (ICT)",
        "b.tech. ict": "B.Tech. (ICT)",
        "b.tech. (ict)": "B.Tech. (ICT)",

        "csai": "B.Tech. (CS and AI)",
        "cs ai": "B.Tech. (CS and AI)",
        "btech csai": "B.Tech. (CS and AI)",
        "b.tech csai": "B.Tech. (CS and AI)",
        "b.tech. (cs and ai)": "B.Tech. (CS and AI)",
        "btech cs and ai": "B.Tech. (CS and AI)",

        "ece": "B.Tech. (ECE-AI)",
        "ece ai": "B.Tech. (ECE-AI)",
        "btech ece": "B.Tech. (ECE-AI)",
        "b.tech. (ece-ai)": "B.Tech. (ECE-AI)",
        "btech ece ai": "B.Tech. (ECE-AI)",

        "evd": "B.Tech. (EVD)",
        "btech evd": "B.Tech. (EVD)",

        "mnc": "B.Tech. (MnC)",
        "btech mnc": "B.Tech. (MnC)",

        "msc it": "M.Sc. (IT)",
        "m.sc. it": "M.Sc. (IT)",
        "it": "M.Sc. (IT)",

        "msc data science": "M.Sc. (Data Science)",
        "m.sc data science": "M.Sc. (Data Science)",
        "data science": "M.Sc. (Data Science)",
        "ds": "M.Sc. (Data Science)",

        "msc agriculture analytics": "M.Sc. (Agriculture Analytics)",
        "m.sc agriculture analytics": "M.Sc. (Agriculture Analytics)",
        "agriculture analytics": "M.Sc. (Agriculture Analytics)",
        "aa": "M.Sc. (Agriculture Analytics)",

        "mtech ict": "M.Tech. (ICT)",
        "m.tech ict": "M.Tech. (ICT)",

        "phd": "Ph.D.",
        "ph.d": "Ph.D."
    }
    
    def _expand_semesters(self, query):
        arabic_to_roman = {
            "1": "I", "2": "II", "3": "III", "4": "IV",
            "5": "V", "6": "VI", "7": "VII", "8": "VIII"
        }
        roman_to_arabic = {v: k for k, v in arabic_to_roman.items()}
        
        # Expand Arabic to Roman, e.g. "semester 1" -> "semester 1 (semester I)"
        for num, roman in arabic_to_roman.items():
            pattern_sem = rf"\b(semester|sem)\s*[-_]?\s*{num}\b"
            if re.search(pattern_sem, query, re.IGNORECASE):
                query = re.sub(pattern_sem, f"\\1 {num} (\\1 {roman})", query, flags=re.IGNORECASE)
                
        # Expand Roman to Arabic, e.g. "semester I" -> "semester I (semester 1)"
        # Use negative lookahead (?!\)) to prevent matching roman numerals inside the newly created (semester I) parentheticals
        for roman in sorted(roman_to_arabic.keys(), key=len, reverse=True):
            num = roman_to_arabic[roman]
            pattern_sem = rf"\b(semester|sem)\s*[-_]?\s*{roman}\b(?!\))"
            if re.search(pattern_sem, query, re.IGNORECASE):
                query = re.sub(pattern_sem, f"\\1 {roman} (\\1 {num})", query, flags=re.IGNORECASE)
                
        return query

    def _build_metadata_filter(
        self,
        plan
    ):
        """Build a Pinecone metadata filter from extracted entities.

        Fix F: multi-value entity lists (e.g. two programs in a comparison
        query) now use the $in operator instead of discarding all but the
        first value via first_value().
        """

        def first_value(value):
            if isinstance(value, list):
                return value[0] if value else None
            return value

        def as_filter(field, value):
            """Return a Pinecone filter clause for one or many values."""
            if isinstance(value, list) and len(value) > 1:
                return {field: {"$in": value}}
            scalar = value[0] if isinstance(value, list) else value
            return {field: {"$eq": scalar}}

        entities = plan.get(
            "entities",
            {}
        )

        course_code_raw = entities.get("course_code")
        course_code = first_value(course_code_raw)

        # Fix F: canonicalise all program values, not just the first one
        program_name_raw = entities.get("program_name")
        if isinstance(program_name_raw, list):
            program_names = [
                p for p in (
                    self._canonical_program_name(p) for p in program_name_raw
                ) if p
            ]
            program_name = program_names[0] if len(program_names) == 1 else (program_names or None)
        else:
            program_name = self._canonical_program_name(program_name_raw)

        if course_code:

            if program_name:
                prog_clause = as_filter("program_name", program_name)
                return {
                    "$and": [
                        {"course_code": {"$eq": course_code}},
                        prog_clause
                    ]
                }

            return {
                "course_code": {
                    "$eq": course_code
                }
            }

        # Fix F: support multi-faculty queries with $in
        faculty_name_raw = entities.get("faculty_name")
        if faculty_name_raw:
            if isinstance(faculty_name_raw, list) and len(faculty_name_raw) > 1:
                return {"faculty_name": {"$in": faculty_name_raw}}
            faculty_name = first_value(faculty_name_raw)
            if faculty_name:
                return {"faculty_name": {"$eq": faculty_name}}

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

        semester = first_value(
            entities.get(
                "semester"
            )
        )

        if program_name and semester:
            prog_clause = as_filter("program_name", program_name)
            return {
                "$and": [
                    prog_clause,
                    {"semester": {"$eq": semester}}
                ]
            }

        if program_name:
            return as_filter("program_name", program_name)

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

        name = re.sub(
            r"\bph\s*d\b",
            "phd",
            name
        )

        return name
    
    def _canonical_program_name(self, name):

        if not name:
            return None

        key = self._normalize_program_name(name)

        canonical = self.PROGRAM_ALIASES.get(key)

        if canonical is None:
            from rapidfuzz import fuzz, process
            aliases_keys = list(self.PROGRAM_ALIASES.keys())
            matches = process.extract(key, aliases_keys, scorer=fuzz.ratio, limit=5)
            if matches:
                best_match = matches[0]
                s1 = best_match[1]
                if s1 >= 80.0:
                    canonical1 = self.PROGRAM_ALIASES[best_match[0]]
                    conflict = False
                    for other_match in matches[1:]:
                        s_other = other_match[1]
                        canonical_other = self.PROGRAM_ALIASES[other_match[0]]
                        if canonical_other != canonical1:
                            if s1 == s_other or (s1 - s_other) < 8.0:
                                conflict = True
                                break
                    if not conflict:
                        canonical = canonical1
                        logger.info(
                            "Fuzzy matched program name '%s' (normalized '%s') to alias '%s' (canonical '%s') with score %.2f",
                            name,
                            key,
                            best_match[0],
                            canonical,
                            s1
                        )

        if canonical is None:
            logger.warning(
                "Unknown program alias '%s' (normalized: '%s'); skipping program metadata filter.",
                name,
                key
            )
            return None

        return canonical

    def _canonical_faculty_name(self, name):
        if not name or not hasattr(self, "faculty_names") or not self.faculty_names:
            return name
        
        # Strip common titles before fuzzy matching
        cleaned = re.sub(r"^(prof\b\.?|professor\b|dr\b\.?|mr\b\.?|ms\b\.?|mrs\b\.?)\s*", "", name, flags=re.IGNORECASE).strip()
        
        # Avoid matching short, generic terms
        if len(cleaned) < 3:
            return name
            
        from rapidfuzz import fuzz, process
        matches = process.extract(cleaned.lower(), self.faculty_names_lower, scorer=fuzz.WRatio, limit=2)
        if not matches:
            return name
            
        best_match = matches[0]
        s1 = best_match[1]
        if s1 >= 80.0:
            if len(matches) == 1:
                corrected = self.faculty_names_map[best_match[0]]
                logger.info("Fuzzy matched faculty name '%s' (cleaned: '%s') to '%s' (Score: %.2f)", name, cleaned, corrected, s1)
                return corrected
            s2 = matches[1][1]
            if s1 == 100.0 or (s1 - s2) >= 8.0:
                corrected = self.faculty_names_map[best_match[0]]
                logger.info("Fuzzy matched faculty name '%s' (cleaned: '%s') to '%s' (Score: %.2f)", name, cleaned, corrected, s1)
                return corrected
                
        return name
            

    def get_context(
        self,
        query,
        history=None
    ):
        original_query = query

        query_lower = query.lower()

        # Fix #6: narrow the rewrite trigger to avoid spurious LLM calls for
        # short but self-contained questions (e.g. "What is the fee?").
        # Rewrite only when:
        #   (a) a pronoun / reference phrase is present in the query, OR
        #   (b) the query is <=3 words AND the first word is a pronoun
        #       (genuine fragment follow-up like "And him?" or "What about it?")
        PRONOUN_REFS = [
            "he", "his", "him", "she", "her", "they", "their", "them",
            "it", "its", "that faculty", "that professor", "that event",
            "that program", "this program", "this event"
        ]
        SHORT_PRONOUN_STARTERS = {
            "he", "his", "him", "she", "her", "they", "their", "them",
            "it", "its", "what about", "how about"
        }
        has_pronoun = any(
            re.search(rf"\b{re.escape(ref)}\b", query_lower)
            for ref in PRONOUN_REFS
        )
        is_short_fragment = (
            len(query.split()) <= 3
            and any(query_lower.startswith(p) for p in SHORT_PRONOUN_STARTERS)
        )
        needs_rewrite = bool(history) and (has_pronoun or is_short_fragment)

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

        # Correct entities inside the plan (e.g. fuzzy match faculty and program names)
        entities = plan.get("entities", {})
        
        # 1. Correct faculty_name
        faculty_val = entities.get("faculty_name")
        if faculty_val:
            if isinstance(faculty_val, list):
                corrected_list = []
                for name in faculty_val:
                    corrected_name = self._canonical_faculty_name(name)
                    corrected_list.append(corrected_name)
                    # Replace the typo name in query and decomposed queries, retaining any title prefix
                    if corrected_name != name:
                        title_match = re.match(r"^(prof\b\.?|professor\b|dr\b\.?|mr\b\.?|ms\b\.?|mrs\b\.?)\s*", name, flags=re.IGNORECASE)
                        title_part = title_match.group(0) if title_match else ""
                        replacement = title_part + corrected_name
                        query = re.sub(re.escape(name), replacement, query, flags=re.IGNORECASE)
                        if plan.get("query_decomposition"):
                            plan["query_decomposition"] = [
                                re.sub(re.escape(name), replacement, dq, flags=re.IGNORECASE)
                                for dq in plan["query_decomposition"]
                            ]
                entities["faculty_name"] = corrected_list
            elif isinstance(faculty_val, str):
                corrected_name = self._canonical_faculty_name(faculty_val)
                if corrected_name != faculty_val:
                    title_match = re.match(r"^(prof\b\.?|professor\b|dr\b\.?|mr\b\.?|ms\b\.?|mrs\b\.?)\s*", faculty_val, flags=re.IGNORECASE)
                    title_part = title_match.group(0) if title_match else ""
                    replacement = title_part + corrected_name
                    query = re.sub(re.escape(faculty_val), replacement, query, flags=re.IGNORECASE)
                    if plan.get("query_decomposition"):
                        plan["query_decomposition"] = [
                            re.sub(re.escape(faculty_val), replacement, dq, flags=re.IGNORECASE)
                            for dq in plan["query_decomposition"]
                        ]
                entities["faculty_name"] = corrected_name

        # 2. Correct program_name
        program_val = entities.get("program_name")
        if program_val:
            if isinstance(program_val, list):
                corrected_list = []
                for prog in program_val:
                    canonical_prog = self._canonical_program_name(prog)
                    if canonical_prog:
                        corrected_list.append(canonical_prog)
                    else:
                        corrected_list.append(prog)
                entities["program_name"] = corrected_list
            elif isinstance(program_val, str):
                canonical_prog = self._canonical_program_name(program_val)
                if canonical_prog:
                    entities["program_name"] = canonical_prog

        corrected_query = query

        query = self._expand_semesters(query)

        entities = plan.get("entities", {})

        event_name = entities.get("event_name")

        program_name = entities.get("program_name")

        # Fix E: only augment the query string with entity names when the
        # planner is confident about the extraction (entity_confidence >= 0.80).
        # A low-confidence wrong extraction (e.g. program_name on a general
        # internship question) biases the embedding toward wrong chunks.
        entity_confidence = plan.get("entity_confidence", 0.5)

        if entity_confidence >= 0.80:
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
                subquery_expanded = self._expand_semesters(subquery)

                # Fix #8: build a sub-query-specific metadata filter.
                # Previously always None, causing sub-queries to scan the full
                # corpus and pull in noise from unrelated programs/faculty.
                sub_metadata_filter = (
                    self._build_metadata_filter(plan)
                )

                sub_results = (
                    self.retriever.retrieve(
                        query=subquery_expanded,
                        top_k=retrieval_top_k,
                        metadata_filter=sub_metadata_filter
                    )
                )

                # Fallback: if the filter yields nothing, retry without it
                if not sub_results and sub_metadata_filter:
                    sub_results = (
                        self.retriever.retrieve(
                            query=subquery_expanded,
                            top_k=retrieval_top_k,
                            metadata_filter=None
                        )
                    )

                sub_reranked = (
                    self.reranker.rerank(
                        query=subquery_expanded,
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

        # ── Entity-based retrieval (professor's algorithm) ─────────────────
        # Fix #3: entity retrieval is now also run for decomposed queries.
        # Previously skipped entirely for comparison/multi-entity queries,
        # which are exactly the ones that benefit most from entity injection.
        if self.entity_retriever:
            entity_chunks = (
                self.entity_retriever.retrieve_by_entities(
                    entities
                )
            )
            if entity_chunks:
                logger.debug(
                    "Entity retriever added %d candidate chunks to pool.",
                    len(entity_chunks),
                )
                results = results + entity_chunks

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
            # Fix A: run a final joint cross-encoder rerank over the merged
            # pool using the original user query (not a sub-query string).
            # Previously, sub-results were merged raw with no joint scoring,
            # so poorly-scored chunks from one sub-query could displace
            # high-quality chunks from another.
            reranked = (
                self.reranker.rerank(
                    query=original_query,
                    results=results,
                    plan=plan
                )
            )

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
                original_query,

            "corrected_query":
                corrected_query,

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