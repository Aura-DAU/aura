from pipeline.retrieval.query_planner import QueryPlanner
from pipeline.retrieval.retriever import Retriever
from pipeline.retrieval.reranker import Reranker
from pipeline.retrieval.context_builder import ContextBuilder

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

        # Load faculty names from metadata.json for fuzzy matching
        import json
        from pathlib import Path
        metadata_path = (
            Path(__file__).resolve().parent.parent
            / "vector_store"
            / "metadata.json"
        )
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

        # Build local index mapping coordinate keys to raw chunks for adjacent chunk expansion
        self.chunk_by_coordinate = {}
        if self.retriever.bm25 and hasattr(self.retriever.bm25, "chunks"):
            for chunk in self.retriever.bm25.chunks:
                doc_id = chunk.get("document_id")
                chunk_idx = chunk.get("chunk_index")
                if doc_id and chunk_idx is not None:
                    self.chunk_by_coordinate[(doc_id, int(chunk_idx))] = chunk


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

        program_name = self._canonical_program_name(
            first_value(
                entities.get(
                    "program_name"
                )
            )
        )

        if course_code:

            if program_name:
                return {
                    "$and": [
                        {
                            "course_code": {
                                "$eq": course_code
                            }
                        },
                        {
                            "program_name": {
                                "$eq": program_name
                            }
                        }
                    ]
                }

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

        decomposed_queries = plan.get(
            "query_decomposition"
        )

        if decomposed_queries:
            all_results = []

            for subquery in decomposed_queries:
                subquery_expanded = self._expand_semesters(subquery)

                # Retrieve dual-path fusion results for the subquery
                sub_results = self._retrieve_dual_path(subquery_expanded, plan)

                # Expand adjacent chunks before reranking
                expanded_sub_results = self._expand_adjacent_chunks(sub_results)

                # Rerank
                sub_reranked = self.reranker.rerank(
                    query=subquery_expanded,
                    results=expanded_sub_results,
                    plan=plan
                )

                all_results.extend(
                    sub_reranked[:3]
                )

            results = all_results
        
        else:
            # Main query retrieval using dual path
            results = self._retrieve_dual_path(query, plan)
            # Expand adjacent chunks
            results = self._expand_adjacent_chunks(results)

        seen = set()
        deduped = []

        for result in results:
            chunk_id = result["id"]
            if chunk_id not in seen:
                deduped.append(result)
                seen.add(chunk_id)

        results = deduped

        if decomposed_queries:
            reranked = results
        else:
            reranked = self.reranker.rerank(
                query=query,
                results=results,
                plan=plan
            )

        # Restrict candidate list to the Top-5 chunks (limit to min of final_top_k and 5)
        final_top_k = min(plan.get("top_k", 5), 5)
        final_chunks = reranked[:final_top_k]

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

    def _expand_adjacent_chunks(self, candidates):
        """
        Retrieves neighboring (i-1 and i+1) chunks for candidate chunks to preserve context.
        """
        expanded_candidates = []
        for cand in candidates:
            metadata = cand.get("metadata", {})
            doc_id = metadata.get("document_id")
            chunk_idx = metadata.get("chunk_index")
            if not doc_id or chunk_idx is None:
                expanded_candidates.append(cand)
                continue
            
            chunk_idx = int(chunk_idx)
            prev_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx - 1))
            next_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx + 1))
            
            parts = []
            if prev_chunk:
                parts.append(prev_chunk.get("text", ""))
            parts.append(metadata.get("text", ""))
            if next_chunk:
                parts.append(next_chunk.get("text", ""))
                
            expanded_text = "\n\n".join(filter(None, parts))
            
            new_cand = dict(cand)
            new_cand["metadata"] = dict(metadata)
            new_cand["metadata"]["text"] = expanded_text
            expanded_candidates.append(new_cand)
            
        return expanded_candidates

    def _retrieve_dual_path(self, query, plan):
        """
        Runs dual-path retrieval: Entity Path (BM25 + Semantic fused via RRF) and
        Semantic Path (Top 50 cosine similarity). Norms both pools using Min-Max and
        combines them with an equal 50/50 weighted sum.
        """
        # 1. Entity Path
        entities = plan.get("entities", {})
        entity_queries = []
        for entity_type, entity_val in entities.items():
            if not entity_val:
                continue
            vals = entity_val if isinstance(entity_val, list) else [entity_val]
            for val in vals:
                val_str = str(val).strip()
                if not val_str:
                    continue
                
                metadata_key = entity_type
                if metadata_key == "program_name":
                    canonical_val = self._canonical_program_name(val_str)
                    if canonical_val:
                        entity_queries.append((val_str, {metadata_key: {"$eq": canonical_val}}))
                    else:
                        entity_queries.append((val_str, None))
                elif metadata_key in ["faculty_name", "event_name", "course_code", "course_name", "semester"]:
                    entity_queries.append((val_str, {metadata_key: {"$eq": val_str}}))
                else:
                    entity_queries.append((val_str, None))

        entity_pool = {}
        for ent_text, ent_filter in entity_queries:
            # Query retriever to get top 3 fused BM25 + dense chunks for this entity
            res_list = self.retriever.retrieve(query=ent_text, top_k=3, metadata_filter=ent_filter)
            if not res_list and ent_filter:
                res_list = self.retriever.retrieve(query=ent_text, top_k=3, metadata_filter=None)
            
            for rank, res in enumerate(res_list, start=1):
                chunk_id = res["id"]
                if chunk_id not in entity_pool:
                    entity_pool[chunk_id] = {
                        "chunk": res,
                        "rrf_score": 0.0
                    }
                entity_pool[chunk_id]["rrf_score"] += 1.0 / (60.0 + rank)

        entity_list = []
        for chunk_id, info in entity_pool.items():
            chunk_item = dict(info["chunk"])
            chunk_item["entity_score"] = info["rrf_score"]
            entity_list.append(chunk_item)

        # Min-Max normalize entity path scores
        if entity_list:
            scores = [c["entity_score"] for c in entity_list]
            min_val = min(scores)
            max_val = max(scores)
            val_range = max_val - min_val
            for c in entity_list:
                c["normalized_score"] = (c["entity_score"] - min_val) / val_range if val_range > 0 else 1.0

        # 2. Semantic Path: Top-50 vector search (using Pinecone index query directly)
        query_embedding = self.retriever.model.encode(
            ["Represent this sentence for searching relevant passages: " + query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        results = self.retriever.index.query(
            vector=query_embedding[0].tolist(),
            top_k=50,
            include_metadata=True,
            filter=None
        )
        semantic_list = []
        for match in results["matches"]:
            semantic_list.append({
                "id": match["id"],
                "score": match["score"],
                "metadata": match["metadata"],
                "semantic_score": match["score"]
            })

        # Min-Max normalize semantic path scores
        if semantic_list:
            scores = [c["semantic_score"] for c in semantic_list]
            min_val = min(scores)
            max_val = max(scores)
            val_range = max_val - min_val
            for c in semantic_list:
                c["normalized_score"] = (c["semantic_score"] - min_val) / val_range if val_range > 0 else 1.0

        # 3. Global 50/50 Fusion
        fused_pool = {}
        for c in entity_list:
            chunk_id = c["id"]
            fused_pool[chunk_id] = {
                "id": chunk_id,
                "metadata": c["metadata"],
                "score": c.get("score", 0.0),
                "entity_norm": c["normalized_score"],
                "semantic_norm": 0.0
            }
        for c in semantic_list:
            chunk_id = c["id"]
            if chunk_id not in fused_pool:
                fused_pool[chunk_id] = {
                    "id": chunk_id,
                    "metadata": c["metadata"],
                    "score": c.get("score", 0.0),
                    "entity_norm": 0.0,
                    "semantic_norm": c["normalized_score"]
                }
            else:
                fused_pool[chunk_id]["semantic_norm"] = c["normalized_score"]

        final_candidates = []
        for chunk_id, info in fused_pool.items():
            final_score = 0.5 * info["entity_norm"] + 0.5 * info["semantic_norm"]
            cand = {
                "id": chunk_id,
                "metadata": info["metadata"],
                "score": info["score"],
                "fusion_score": final_score
            }
            final_candidates.append(cand)

        # Sort candidates by final fusion score descending
        final_candidates.sort(key=lambda x: x["fusion_score"], reverse=True)
        return final_candidates