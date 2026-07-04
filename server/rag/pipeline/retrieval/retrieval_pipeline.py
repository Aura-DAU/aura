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
        "ph.d": "Ph.D.",

        # Fix RP3: BS-MS dual degree programs were entirely missing from
        # PROGRAM_ALIASES, so "fee for BS-MS" / "BS-MS admissions" queries
        # produced no program_name entity → no metadata filter → noisy retrieval.
        "bs ms": "BS-MS (Data Science & Artificial Intelligence)",
        "bs-ms": "BS-MS (Data Science & Artificial Intelligence)",
        "bs ms ds ai": "BS-MS (Data Science & Artificial Intelligence)",
        "bs ms data science": "BS-MS (Data Science & Artificial Intelligence)",
        "bs ms dsai": "BS-MS (Data Science & Artificial Intelligence)",
        "bs ms artificial intelligence": "BS-MS (Data Science & Artificial Intelligence)",
        "bs ms it": "BS-MS (Information Technology)",
        "bs ms information technology": "BS-MS (Information Technology)",

        # MDes variants
        "mdes": "M.Des.",
        "m des": "M.Des.",
        "m.des": "M.Des.",
        "mdes cd": "M.Des. (CD)",
        "mdes iuxd": "M.Des. (IUxD)",
        "m.des. cd": "M.Des. (CD)",
        "m.des. iuxd": "M.Des. (IUxD)",
        "design": "M.Des.",

        # MTech EC
        "mtech ec": "M.Tech. (EC)",
        "m.tech ec": "M.Tech. (EC)",
        "mtech ece": "M.Tech. (EC)",

        # MTech CS ML
        "mtech cs ml": "M.Tech. (CS and ML)",
        "mtech cs": "M.Tech. (CS and ML)",
        "mtech ml": "M.Tech. (CS and ML)",

        # Fix AL1: bare "mtech"/"m.tech" without specialization suffix is a valid
        # query term (e.g. "what is the M.Tech fee?"). Previously normalized to
        # "mtech" → alias miss → filter skipped → top_k stays at 5 → answer buried.
        # Map to a sentinel "M.Tech." so the alias hit triggers the top_k boost.
        "mtech": "M.Tech.",
        "m tech": "M.Tech.",

        # MSc IT variants
        "msc it": "M.Sc. (IT)",
        "m.sc it": "M.Sc. (IT)",
        "msc information technology": "M.Sc. (IT)",

        # BTech with full spellings
        "b tech ict": "B.Tech. (ICT)",
        "b tech csai": "B.Tech. (CS and AI)",
        "b tech ece": "B.Tech. (ECE-AI)",
        "b tech evd": "B.Tech. (EVD)",
        "b tech mnc": "B.Tech. (MnC)",
        "computer science and artificial intelligence": "B.Tech. (CS and AI)",
        "electronics and communication": "B.Tech. (ECE-AI)",
        "mathematics and computing": "B.Tech. (MnC)",

        # Fix AL1 (cont.): bare program abbreviations used when no specialization given
        "btech": "B.Tech.",
        "b tech": "B.Tech.",
        "msc": "M.Sc.",
        "m sc": "M.Sc.",
        "mtech ict": "M.Tech. (ICT)",
        "msc data science": "M.Sc. (Data Science)",
        "msc agriculture analytics": "M.Sc. (Agriculture Analytics)",
        "phd regular": "Ph.D.",
        "phd part time": "Ph.D.",
        "doctoral": "Ph.D."
    }

    # Fix AL1-SENTINEL: broad program sentinels are valid alias targets
    # (e.g. "mtech" → "M.Tech.") but they do NOT exist as values in the
    # Pinecone index — the index only stores specific specialisations like
    # "M.Tech. (ICT)". Building a filter {"program_name": {"$eq": "M.Tech."}}
    # therefore always returns zero results, and the fallback filter-free
    # search then runs with top_k=5 instead of the intended 15.
    # Listing them here lets both _build_metadata_filter and the
    # alias_resolved check treat them as "unresolved / broad".
    BROAD_PROGRAM_SENTINELS = {"B.Tech.", "M.Tech.", "M.Sc.", "M.Des."}

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

    def _apply_dls_filter(self, filter_dict, allowed_roles):
        if not allowed_roles:
            return filter_dict
        role_clause = {"authorization": {"$in": allowed_roles}}
        if filter_dict:
            if "$and" in filter_dict:
                # Ensure we don't mutate the original list if it's reused
                new_and = list(filter_dict["$and"])
                new_and.append(role_clause)
                return {"$and": new_and}
            return {"$and": [filter_dict, role_clause]}
        return role_clause

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

        # Fix F: canonicalise all program values, not just the first one.
        # Fix AL1-SENTINEL: after canonicalisation, strip broad sentinel values
        # ("B.Tech.", "M.Tech.", "M.Sc.", "M.Des.") so they never produce a
        # Pinecone filter clause — those strings do not exist in the index.
        program_name_raw = entities.get("program_name")
        if isinstance(program_name_raw, list):
            program_names = [
                p for p in (
                    self._canonical_program_name(p) for p in program_name_raw
                ) if p
            ]
            # Remove broad sentinels from the list
            program_names = [p for p in program_names if p not in self.BROAD_PROGRAM_SENTINELS]
            program_name = program_names[0] if len(program_names) == 1 else (program_names or None)
        else:
            program_name = self._canonical_program_name(program_name_raw)
            # A broad sentinel must not become a filter clause
            if program_name in self.BROAD_PROGRAM_SENTINELS:
                program_name = None

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
        history=None,
        user_role="public"
    ):
        from pipeline.retrieval.rbac import get_allowed_roles
        allowed_roles = get_allowed_roles(user_role)

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

        # Fix RP-MYTH: replaces the old static MYTH_BUST_PATTERNS keyword list
        # that lived in aura_chat.py. The query_planner LLM already classifies
        # every query's intent and entities — it is the single correct place
        # to also flag claim-verification framing ("is this true", "I was told
        # that...", etc.), since that classification generalizes to any phrasing
        # in any language/dialect mix the planner sees, unlike a static list of
        # English phrases. If the plan signals claim verification, append a
        # retrieval-side directive so the matched chunk's policy/rule language
        # ranks higher — this also lets the answer generator give a direct
        # verdict instead of exploring multiple interpretations (Type9 latency).
        if plan.get("is_claim_verification"):
            query = query + " policy rule regulation verify"

        # Fix RP-FEE: replaces the old static FEE_KEYWORDS list. The retrieval
        # intent "admissions_information" combined with required_sections
        # already containing "Fee"/"Fees Structure"/"Tuition" (set generically
        # by the planner's few-shot examples, not by string-matching here) is
        # sufficient signal — no separate keyword list needed. We simply
        # surface the planner's own required_sections into the BM25 query
        # so its classification has retrieval-side effect.
        plan_required_sections = plan.get("retrieval_hints", {}).get("required_sections", [])
        if plan_required_sections:
            # Append a small number of the most specific (longest) section
            # names so BM25 keyword matching benefits from exactly what the
            # planner identified as relevant — generalizes to ANY section
            # heading the planner names (Fee, Dean of Academic Programs,
            # Board of Studies, etc.) without a static list of any kind.
            top_sections = sorted(plan_required_sections, key=len, reverse=True)[:3]
            query = query + " " + " ".join(top_sections)

        # Fix RP-VOCAB: replaces the old static LAUNDRY_KEYWORDS / MOVEIN_KEYWORDS
        # lists. The planner's expanded_terms field (Fix QP7) does the same
        # informal-to-formal vocabulary translation generically, per-query,
        # using the LLM's own knowledge of DAU document phrasing — instead of
        # a fixed Python list that only covers terms already seen in testing.
        # This is the single mechanism that handles ANY future vocabulary gap
        # (dhobi, mattress, role-name confusion, or anything not yet tested)
        # without requiring a code change.
        expanded_terms = plan.get("expanded_terms", [])
        if expanded_terms:
            query = query + " " + " ".join(expanded_terms[:5])

        # Fix RP-COMPLETE: negation ("What is NOT X") and enumeration
        # ("how many total X") questions need the FULL set of relevant
        # chunks, not just the top-5 semantically closest ones — otherwise
        # the LLM only sees a partial list and cannot correctly identify
        # what is missing or excluded. Widen top_k generically using the
        # planner's requires_complete_list signal rather than hardcoding
        # per-entity-type retrieval counts.
        if plan.get("requires_complete_list"):
            plan["top_k"] = max(plan.get("top_k", 5), 12)

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
        
        # Apply DLS Layer A
        metadata_filter = self._apply_dls_filter(metadata_filter, allowed_roles)

        # Fix DEG1: dead-end guard for policy version/metadata queries.
        retrieval_intent = plan.get("retrieval_intent", "general")
        if retrieval_intent == "policy_version" and metadata_filter:
            # We still need the DLS filter even if intent is policy_version
            metadata_filter = self._apply_dls_filter(None, allowed_roles)

        # Fix TY1: temporal year anchor — if the planner extracted a rule_year
        # (e.g. "2024-25") from the query, inject it into the retrieval query
        # so BM25 keyword matching prioritises documents whose title or heading
        # contains that year string. This fixes Om report failures where
        # "under the 2024-25 PhD rules" retrieves the 2019-20 document instead.
        rule_year = plan.get("entities", {}).get("rule_year")
        if rule_year:
            # Augment the query string so BM25 scores year-matching chunks higher
            query = query + " " + rule_year
            # Also boost it as a required section heading in the plan hints
            plan.setdefault("retrieval_hints", {})
            existing_sections = plan["retrieval_hints"].get("required_sections", [])
            if rule_year not in existing_sections:
                existing_sections.append(rule_year)
            plan["retrieval_hints"]["required_sections"] = existing_sections

        decomposed_queries = plan.get(
            "query_decomposition"
        )

        if decomposed_queries:
            all_results = []

            # Fix Bug1: retrieval_top_k was referenced but never defined,
            # causing a NameError that silently crashed the decomposed-query
            # branch and returned zero results ("not in database" false positive).
            # Use plan["top_k"] (already boosted for multi-entity queries) or
            # fall back to 5 per sub-query.
            # Fix AL2: when the metadata filter will be None (because program_name
            # canonicalized to None — bare alias like "M.Tech" with no specialization),
            # raise top_k to 15 so the answer isn't buried under noise.
            # The filter being None means the entire index is searched; top_k=5
            # is far too narrow for broad-corpus sub-queries.
            base_top_k = plan.get("top_k", 5)
            # Fix AL1-SENTINEL: alias_resolved must be False for broad sentinels
            # ("M.Tech.", "B.Tech.", etc.) so the top_k=15 boost fires.
            # The old code treated any non-None canonical as resolved, but
            # sentinels are non-None yet still unresolved — they only mean
            # "user said mtech without specifying a specialisation".
            raw_program = plan.get("entities", {}).get("program_name", "")
            canonical_program = self._canonical_program_name(raw_program) if raw_program else None
            alias_resolved = (
                canonical_program is not None
                and canonical_program not in self.BROAD_PROGRAM_SENTINELS
            )
            retrieval_top_k = base_top_k if alias_resolved else max(base_top_k, 15)

            for subquery in decomposed_queries:
                subquery_expanded = self._expand_semesters(subquery)

                # Fix #8: build a sub-query-specific metadata filter.
                # Previously always None, causing sub-queries to scan the full
                # corpus and pull in noise from unrelated programs/faculty.
                sub_metadata_filter = (
                    self._build_metadata_filter(plan)
                )
                sub_metadata_filter = self._apply_dls_filter(sub_metadata_filter, allowed_roles)

                sub_results = (
                    self.retriever.retrieve(
                        query=subquery_expanded,
                        top_k=retrieval_top_k,
                        metadata_filter=sub_metadata_filter
                    )
                )

                # Fallback: if the filter yields nothing, retry without it
                if not sub_results and sub_metadata_filter:
                    # Still apply DLS filter even in fallback!
                    fallback_filter = self._apply_dls_filter(None, allowed_roles)
                    sub_results = (
                        self.retriever.retrieve(
                            query=subquery_expanded,
                            top_k=retrieval_top_k,
                            metadata_filter=fallback_filter,
                            allowed_roles=allowed_roles
                        )
                    )

                # Fix CP1: for cross-policy comparison queries, even if the
                # filtered retrieval returns some results, those may all be
                # from ONE policy. If this sub-query is retrieving the second
                # leg and results overlap heavily with already-seen chunk IDs,
                # also retry filter-free to maximise distinct coverage.
                if sub_results and sub_metadata_filter:
                    already_seen_ids = {r["id"] for r in all_results}
                    new_in_sub = [r for r in sub_results if r["id"] not in already_seen_ids]
                    if len(new_in_sub) == 0:
                        # All sub-results already collected — retry without filter
                        fallback_filter = self._apply_dls_filter(None, allowed_roles)
                        extra = self.retriever.retrieve(
                            query=subquery_expanded,
                            top_k=retrieval_top_k,
                            metadata_filter=fallback_filter,
                            allowed_roles=allowed_roles
                        )
                        new_extra = [r for r in extra if r["id"] not in already_seen_ids]
                        if new_extra:
                            sub_results = new_extra

                sub_reranked = (
                    self.reranker.rerank(
                        query=subquery_expanded,
                        results=sub_results,
                        plan=plan
                    )
                )

                # Fix SR1: raised per-sub-query cap from 3 → 4 for multi-entity
                # (comparison) queries. With 3 chunks per sub-query and 2 sub-
                # queries, the joint rerank pool was only 6 items — often not
                # enough distinct coverage when one leg returns weak results.
                # 4 per sub-query gives an 8-item joint pool for 2-way comparisons.
                sub_limit = 4 if plan.get("multi_entity_query") else 3
                all_results.extend(
                    sub_reranked[:sub_limit]
                )

            results = all_results
        
        else:
            # Main query retrieval using dual path
            results = self._retrieve_dual_path(query, plan, allowed_roles)
            # Fix J2: use a wider context window for policy_version queries
            # so that version history sections (which may be 1-2 chunks after
            # the main policy heading) are always included in context.
            expand_window = 2 if retrieval_intent == "policy_version" else 1
            results = self._expand_adjacent_chunks(results, window=expand_window)
        # ── Entity-based retrieval (professor's algorithm) ─────────────────
        # Merge entity-matched chunks (Step 2: Chunks→Triples→Entity) with
        # the vector/BM25 results into a unified chunk pool for reranking.
        # Fix RP1: previously two separate blocks existed — one guarded by
        # `not decomposed_queries` and a second unconditional one. For
        # non-decomposed queries both ran, injecting entity chunks twice
        # (before dedup). Collapsed into a single unconditional block so
        # entity retrieval runs exactly once for all query types.
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
                deduped.append(result)
                seen.add(chunk_id)

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
            reranked = self.reranker.rerank(
                query=query,
                results=results,
                plan=plan
            )

        # Fix TK1: previously capped at min(plan["top_k"], 5) which destroyed
        # the multi-entity boost (num_entities*3 was always clamped back to 5).
        # For multi-entity queries 2 entities need at least 3 chunks each = 6.
        # Cap raised to 8 to give comparison queries enough chunks while staying
        # within the context token budget (3000 tokens ≈ 8-9 chunks).
        max_final = 8 if plan.get("multi_entity_query") else 5
        final_top_k = min(plan.get("top_k", 5), max_final)
        final_chunks = reranked[:final_top_k]

        built = (
            self.builder.build(
                final_chunks,
                retrieval_intent=retrieval_intent
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

    def _expand_adjacent_chunks(self, candidates, window=1):
        """
        Retrieves neighboring chunks (window chunks before and after) for each
        candidate to preserve context. window=1 is the default; use window=2
        for policy_version queries to capture version history sections that may
        be one or two chunks away from the main policy chunk.
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
            parts = []

            # Collect preceding chunks within window
            for offset in range(window, 0, -1):
                prev_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx - offset))
                if prev_chunk:
                    parts.append(prev_chunk.get("text", ""))

            parts.append(metadata.get("text", ""))

            # Collect following chunks within window
            for offset in range(1, window + 1):
                next_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx + offset))
                if next_chunk:
                    parts.append(next_chunk.get("text", ""))

            expanded_text = "\n\n".join(filter(None, parts))

            new_cand = dict(cand)
            new_cand["metadata"] = dict(metadata)
            new_cand["metadata"]["text"] = expanded_text
            expanded_candidates.append(new_cand)

        return expanded_candidates

    def _retrieve_dual_path(self, query, plan, allowed_roles):
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
            # Apply DLS filter to entity filter
            ent_filter = self._apply_dls_filter(ent_filter, allowed_roles)
            # Query retriever to get top 3 fused BM25 + dense chunks for this entity
            res_list = self.retriever.retrieve(query=ent_text, top_k=3, metadata_filter=ent_filter, allowed_roles=allowed_roles)
            if not res_list and ent_filter:
                fallback_filter = self._apply_dls_filter(None, allowed_roles)
                res_list = self.retriever.retrieve(query=ent_text, top_k=3, metadata_filter=fallback_filter, allowed_roles=allowed_roles)
            
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
        semantic_filter = self._apply_dls_filter(self._build_metadata_filter(plan), allowed_roles)
        query_embedding = self.retriever.model.encode(
            ["Represent this sentence for searching relevant passages: " + query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        results = self.retriever.index.query(
            vector=query_embedding[0].tolist(),
            top_k=50,
            include_metadata=True,
            filter=semantic_filter
        )
        
        if not results["matches"] and semantic_filter:
            # Fallback if no results with semantic_filter (but still keep DLS filter)
            fallback_filter = self._apply_dls_filter(None, allowed_roles)
            results = self.retriever.index.query(
                vector=query_embedding[0].tolist(),
                top_k=50,
                include_metadata=True,
                filter=fallback_filter
            )
        semantic_list = []
        for match in results["matches"]:
            semantic_list.append({
                "id": match["id"],
                "score": match["score"],
                # Fix RP2: cosine_score explicitly stored so the confidence
                # router in aura_chat.py can read it via c.get("cosine_score").
                # Previously dual-path candidates only had "score"/"fusion_score"
                # so the router always saw top_cosine=0.0 and relied entirely
                # on top_cross for routing decisions.
                "cosine_score": match["score"],
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
        # Fix RP2 (cont.): cosine_score is tracked through the fused pool
        # so it survives into the final_candidates list for the router.
        fused_pool = {}
        for c in entity_list:
            chunk_id = c["id"]
            fused_pool[chunk_id] = {
                "id": chunk_id,
                "metadata": c["metadata"],
                "score": c.get("score", 0.0),
                "cosine_score": c.get("cosine_score", 0.0),
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
                    "cosine_score": c.get("cosine_score", 0.0),
                    "entity_norm": 0.0,
                    "semantic_norm": c["normalized_score"]
                }
            else:
                fused_pool[chunk_id]["semantic_norm"] = c["normalized_score"]
                # Prefer the semantic path's cosine_score (it's the raw Pinecone value)
                fused_pool[chunk_id]["cosine_score"] = c.get("cosine_score", 0.0)

        final_candidates = []
        for chunk_id, info in fused_pool.items():
            final_score = 0.5 * info["entity_norm"] + 0.5 * info["semantic_norm"]
            cand = {
                "id": chunk_id,
                "metadata": info["metadata"],
                "score": info["score"],
                "cosine_score": info.get("cosine_score", 0.0),
                "fusion_score": final_score
            }
            final_candidates.append(cand)

        # Sort candidates by final fusion score descending
        final_candidates.sort(key=lambda x: x["fusion_score"], reverse=True)
        return final_candidates