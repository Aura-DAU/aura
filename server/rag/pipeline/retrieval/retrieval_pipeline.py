from pipeline.retrieval.query_planner import QueryPlanner
from pipeline.retrieval.retriever import Retriever
from pipeline.retrieval.reranker import Reranker
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.retrieval.entity_retriever import EntityRetriever
from pipeline.retrieval.rbac import get_allowed_roles

import os
import re
import logging
import datetime

logger = logging.getLogger(__name__)

RECENCY_INTENT_RE = re.compile(
    r"\b(latest|newest|most recent|most up[- ]to[- ]date|up[- ]to[- ]date|"
    r"this semester|current semester|this year|current year|currently|"
    r"upcoming|recently updated|"
    r"new (?:schedule|timetable|syllabus|curriculum|policy|rules|circular|"
    r"notice|semester|calendar))\b",
    re.IGNORECASE,
)

# Canonical program_name for the ICT-CS specialisation. Matches the title the
# corpus uses on the programmes-of-study page ("B.Tech. (Honours) in ICT with
# minor in Computational Science"), which is what ingestion writes into
# program_name for that document.
ICT_CS_PROGRAM_NAME = "B.Tech. (Honours) in ICT with minor in Computational Science"

# branch_id values, as derived by api.academic_scope_persist, mapped to the
# canonical program_name that identifies that branch's own documents. Used to
# widen — never narrow — the program entity inferred from a student's scope.
BRANCH_PROGRAM_NAMES = {
    "ict-cs": ICT_CS_PROGRAM_NAME,
}

class RetrievalPipeline:

    def __init__(self):

        self.planner = QueryPlanner()

        self.retriever = Retriever()

        self.reranker = Reranker()

        self.builder = ContextBuilder()

        from pipeline.retrieval.query_rewriter import QueryRewriter
        self.rewriter = QueryRewriter()

        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=2)

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
                raw_faculty = set()
                for chunk in chunks:
                    fn = chunk.get("faculty_name")
                    if isinstance(fn, str) and fn.strip():
                        raw_faculty.add(fn.strip())
                    elif isinstance(fn, list):
                        for item in fn:
                            if isinstance(item, str) and item.strip():
                                raw_faculty.add(item.strip())
                self.faculty_names = sorted(list(raw_faculty))
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

        # CHAT-02: ICT-CS is a specialisation of B.Tech. (ICT), not a separate
        # programme (see academic_scope_persist and the ingestion extractor).
        # It gets its own canonical program_name so ICT-CS-specific documents
        # can be preferentially matched, while the academic-scope filter still
        # admits generic btech-ict material for an ICT-CS student.
        "ict cs": ICT_CS_PROGRAM_NAME,
        "ictcs": ICT_CS_PROGRAM_NAME,
        "btech ict cs": ICT_CS_PROGRAM_NAME,
        "b tech ict cs": ICT_CS_PROGRAM_NAME,
        "ict honours": ICT_CS_PROGRAM_NAME,
        "honours ict": ICT_CS_PROGRAM_NAME,
        "btech honours ict": ICT_CS_PROGRAM_NAME,
        "btech honours in ict": ICT_CS_PROGRAM_NAME,
        "ict with minor in computational science": ICT_CS_PROGRAM_NAME,
        "btech honours in ict with minor in computational science": ICT_CS_PROGRAM_NAME,
        "computational science": ICT_CS_PROGRAM_NAME,
        "ict computational science": ICT_CS_PROGRAM_NAME,

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
        "phd regular": "Ph.D.",
        "phd part time": "Ph.D.",
        "doctoral": "Ph.D."
    }

    BROAD_PROGRAM_SENTINELS = {
        "M.Tech.", "B.Tech.", "M.Sc.", "M.Des.", "Ph.D."
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

    @staticmethod
    def _canonical_semester_values(semester_raw):
        if not semester_raw:
            return []
        sem_str = str(semester_raw).strip()
        arabic_to_roman = {
            "1": "I", "2": "II", "3": "III", "4": "IV",
            "5": "V", "6": "VI", "7": "VII", "8": "VIII"
        }
        roman_to_arabic = {v: k for k, v in arabic_to_roman.items()}
        m_digit = re.search(r"\b([1-8])\b", sem_str)
        m_roman = re.search(r"\b(VIII|VII|VI|V|IV|III|II|I)\b", sem_str, re.IGNORECASE)
        digit = m_digit.group(1) if m_digit else None
        roman = m_roman.group(1).upper() if m_roman else None
        if not digit and roman:
            digit = roman_to_arabic.get(roman)
        elif digit and not roman:
            roman = arabic_to_roman.get(digit)
        variants = []
        if roman:
            variants.extend([f"Semester {roman}", roman])
        if digit:
            variants.extend([f"Semester {digit}", f"Sem {digit}", digit])
        seen = set()
        out = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out or [sem_str]

    def _build_metadata_filter(
        self,
        plan,
        query=None
    ):
        """Build an entity-priority metadata filter dictionary from planner entities when entity_confidence >= 0.80."""
        entity_confidence = plan.get("entity_confidence", 1.0) if isinstance(plan, dict) else 1.0
        if entity_confidence < 0.80:
            return None

        entities = plan.get("entities", {}) if isinstance(plan, dict) else {}
        if not entities:
            return None

        def _make_clause(field, raw_val):
            if not raw_val:
                return None
            if field == "program_name":
                if isinstance(raw_val, list):
                    progs = [p for p in (self._canonical_program_name(item) for item in raw_val) if p]
                    val = progs if progs else raw_val
                else:
                    canonical_prog = self._canonical_program_name(raw_val)
                    val = [canonical_prog] if canonical_prog else [raw_val]
            elif field == "semester":
                if isinstance(raw_val, list):
                    sem_vals = []
                    for item in raw_val:
                        sem_vals.extend(self._canonical_semester_values(item))
                    val = sorted(list(set(sem_vals))) if sem_vals else raw_val
                else:
                    sem_vals = self._canonical_semester_values(raw_val)
                    val = sem_vals if sem_vals else [raw_val]
            else:
                val = raw_val

            if isinstance(val, (list, tuple, set)):
                val_list = [str(x).strip() for x in val if x and str(x).strip()]
                if val_list:
                    return {field: {"$in": sorted(list(set(val_list)))}}
            else:
                s_val = str(val).strip()
                if s_val:
                    return {field: {"$in": [s_val]}}
            return None

        # Priority 1: course_code (highest specificity)
        if entities.get("course_code"):
            clause = _make_clause("course_code", entities.get("course_code"))
            if clause:
                return clause

        # Priority 2: faculty_name
        if entities.get("faculty_name"):
            clause = _make_clause("faculty_name", entities.get("faculty_name"))
            if clause:
                return clause

        # Priority 3: event_name (+ optional semester)
        if entities.get("event_name"):
            clauses = []
            ev_clause = _make_clause("event_name", entities.get("event_name"))
            if ev_clause:
                clauses.append(ev_clause)
                if entities.get("semester"):
                    sem_clause = _make_clause("semester", entities.get("semester"))
                    if sem_clause:
                        clauses.append(sem_clause)
                return clauses[0] if len(clauses) == 1 else {"$and": clauses}

        # Priority 4: program_name (+ optional semester)
        if entities.get("program_name"):
            clauses = []
            prog_clause = _make_clause("program_name", entities.get("program_name"))
            if prog_clause:
                clauses.append(prog_clause)
                if entities.get("semester"):
                    sem_clause = _make_clause("semester", entities.get("semester"))
                    if sem_clause:
                        clauses.append(sem_clause)
                return clauses[0] if len(clauses) == 1 else {"$and": clauses}

        # Priority 5: semester only
        if entities.get("semester"):
            clause = _make_clause("semester", entities.get("semester"))
            if clause:
                return clause

        return None

    def _recency_filter(self, plan, query):
        """
        Issue 2 fix: turn "latest/current/this semester"-type queries into a
        hard `document_year >= threshold` filter sent to the vector DB,
        instead of relying only on the reranker's soft temporal_boost.

        An explicit rule_year entity (e.g. "under the 2022-23 PhD rules")
        means the user named a specific — possibly non-current — year on
        purpose, so it always wins over the generic "latest" heuristic and
        no hard filter is applied.

        threshold = current_year - 1 rather than exactly current_year: chunk
        document_year is the *start* year of an academic-year label (e.g.
        "2025-26" -> 2025), so a query made partway into 2026 about "this
        semester" can legitimately hit a chunk tagged 2025. Using a 1-year
        tolerance window avoids punishing that labeling convention while
        still hard-excluding anything older.
        """
        entities = plan.get("entities", {}) if isinstance(plan, dict) else {}
        if entities.get("rule_year"):
            return None
        if not RECENCY_INTENT_RE.search(query or ""):
            return None
        threshold = datetime.datetime.now().year - 1
        return {"document_year": {"$gte": threshold}}

    def _scatter_gather_filter(self, plan, query):
        """
        Fix for Issue 4: Poor Scatter-Gather Retrieval (Top-K Truncation).
        When the user asks broad listing queries (e.g., 'What programs are offered?' 
        or 'Who is doing research in NLP?'), vector search top-K will truncate lists.
        By emitting a hard metadata filter, we can retrieve exactly the overview/list chunks.
        """
        q_lower = (query or "").lower()
        
        # Broad Program listing queries
        if "what programs" in q_lower or "list all programs" in q_lower or "which programs" in q_lower or "types of programs" in q_lower:
            return {"category": {"$in": ["program_list"]}}
            
        # Broad Research Domain listing queries
        # If the planner extracted a research domain or we detect domain keywords
        # (Assuming research queries have intent = 'research' or 'faculty')
        intent = plan.get("intent") if isinstance(plan, dict) else None
        if intent in ("research", "faculty"):
            if "research in " in q_lower or "working on " in q_lower or "who does" in q_lower:
                # In a robust implementation we'd check if an extracted research_domain entity exists,
                # but since we didn't add it to the planner schema, we just rely on the LLM's keyword matching
                pass
                
        return None

    @staticmethod
    def _combine_filters(*filters):
        active = [item for item in filters if item]
        if not active:
            return None
        return active[0] if len(active) == 1 else {"$and": active}

    @staticmethod
    def _academic_scope_filter(academic_scope):
        if academic_scope is None:
            return None
        scoped = {
            "$and": [
                {"applicability_scope": {"$in": ["programme", "curriculum"]}},
                {"programme_id": {"$eq": academic_scope.programme_id}},
                {"degree_level": {"$eq": academic_scope.degree_level}},
                {"admission_year_from": {"$lte": academic_scope.admission_year}},
                {"admission_year_to": {"$gte": academic_scope.admission_year}},
            ]
        }
        # Course documents (structure, catalog, per-course policy) are public
        # course-catalog information: a signed-in student may look up any
        # course, exactly as a signed-out guest can, so they are admitted
        # unconditionally rather than gated by registered_course_codes. They
        # are keyed by course_code, not by programme_id/degree_level/
        # admission_year (they never populate those fields — the same course is
        # often shared across programmes), so they need their own clause
        # instead of being forced through the programme/curriculum clause
        # above, which they can never satisfy.
        or_clauses = [
            {"applicability_scope": {"$eq": "global"}},
            {"applicability_scope": {"$eq": "course"}},
            scoped,
        ]

        # A missing branch on a document means programme-wide applicability;
        # branch equality is enforced by the post-retrieval predicate when a
        # document declares one, without excluding those programme-wide docs.
        return {"$or": or_clauses}

    @staticmethod
    def _requires_academic_scope(plan: dict) -> bool:
        # Bug fix (RAG_Detailed_Report Aug 2026 -- Q1-Q9 all abstaining with
        # "I don't have your academic programme details on file yet..." on
        # plain university-wide policy questions like "minimum attendance
        # requirement", "what does a DX grade mean", "who maintains
        # attendance records"): this used to fire for ANY category=="academics"
        # plan regardless of retrieval_intent, which is far broader than the
        # documented intent just above (see the abstention call site's own
        # comment: "Abstain only for personal/'my programme' curriculum
        # questions"). Universal rules/policy-version lookups apply
        # identically to every student and don't need the asker's own
        # programme/branch/year resolved -- only genuine "my programme's
        # curriculum" lookups do. Named-programme/course questions still
        # bypass this via _has_explicit_programme_context below regardless.
        return plan.get("retrieval_intent") in {"program_curriculum", "program_overview"}

    # Matches explicit programme abbreviations, year ordinals, or semester
    # numbers in the raw query text — a signal that the question is about a
    # public timetable/curriculum document, not the user's own ERP record.
    # Referenced by the abstention gate in get_context().
    _EXPLICIT_PROGRAMME_IN_QUERY_RE = re.compile(
        r"\b(?:"
        r"b\.?tech|m\.?tech|m\.?sc|bs[\s\-]ms|b\.?des|m\.?des|ph\.?d|"
        r"ict(?:[\s\-]cs)?|mnc|evd|ece[\s\-]ai|cs[\s\-]ai|data\s+science|"
        r"first[\s-]year|second[\s-]year|third[\s-]year|fourth[\s-]year|"
        r"1st[\s-]year|2nd[\s-]year|3rd[\s-]year|4th[\s-]year|"
        r"semester\s+[1-8]|sem(?:ester)?\s+[1-8]|\bsem\s*[1-8]\b|"
        r"postgraduate|undergraduate|all\s+(?:students?|branches?|programs?)"
        r")\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _has_explicit_programme_context(plan: dict) -> bool:
        """True when the query already has enough non-personal context that
        the academic-scope gate isn't needed — no personal scope required."""
        entities = plan.get("entities") or {}
        if (
            entities.get("program_name")
            or entities.get("course_code")
            or entities.get("course_name")
        ):
            return True
        # Fix #4 (RAG_Final_Benchmark_Report): "Can you explain 'NIRF
        # Classification of Five-Year Dual Degree Students'?" and similar
        # self-contained "explain/define this named policy or
        # classification" questions were falling through to the
        # ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE bail-out ("I don't have your
        # academic programme details on file yet...") purely because
        # category=="academics", even though the question asks to explain
        # a rule in general, not "how does this apply to me" — it doesn't
        # need the asker's own year/semester/branch at all. intent=="general"
        # is the planner's own established signal for exactly this: a
        # non-personalized, definitional/comparison query (see the library
        # borrowing-limit examples above), so it's a reliable bypass here
        # too, without loosening the gate for genuinely personal curriculum
        # questions like "what electives can I take this semester".
        if plan.get("intent") == "general":
            return True
        return False

    @staticmethod
    def _eligible_results(results: list[dict], academic_scope) -> list[dict]:
        if academic_scope is None:
            return results
        return [
            result for result in results
            if academic_scope.document_is_eligible(result.get("metadata", {}))
        ]

    def _scope_program_names(self, academic_scope):
        """Program entity value(s) implied by a student's own academic scope.

        For a student on a branch that has its own corpus material (today only
        ICT-CS), this returns BOTH the branch's canonical name and the parent
        programme's, branch-specific first. That ordering matters and the list
        matters:

        - As a metadata filter, a multi-value list becomes ``$in``, so it
          widens the candidate set instead of pinning it to one program_name.
          Returning the branch name alone would exclude the generic
          B.Tech. (ICT) material that still applies to an ICT-CS student.
        - In `_retrieve_dual_path`, each value gets its own entity retrieval
          whose results are fused by RRF, so ICT-CS-specific documents get an
          independent shot at the pool rather than competing inside a single
          B.Tech. (ICT) query they would usually lose.
        """
        programme_id = getattr(academic_scope, "programme_id", None)
        if not programme_id:
            return []
        parent = self._canonical_program_name(programme_id)
        branch_name = BRANCH_PROGRAM_NAMES.get(getattr(academic_scope, "branch_id", None))
        names = [name for name in (branch_name, parent) if name]
        # Preserve order while dropping duplicates.
        return list(dict.fromkeys(names))

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
        user_role: str = "public",
        academic_scope=None,
        identity=None,
        title_hint: str = None,
    ):
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
            "that program", "this program", "this event",
            "the same one", "the same"
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

        rewritten_query = query
        if needs_rewrite:
            query = (
                self.rewriter.rewrite(
                    query,
                    history,
                    academic_scope=academic_scope,
                )
            )
            rewritten_query = query

        print("\n" + "=" * 60)
        print("===== QUERY =====")
        print(f"Original Query: {original_query}")
        print(f"Rewritten Query (QueryRewriter): {rewritten_query}")
        print("=" * 60)

        # Submit the planning LLM call to executor
        future_plan = self.executor.submit(self.planner.plan, query, academic_scope, history)

        # Scope-derived programme names are soft retrieval signals. Keeping them
        # separate from planner entities lets the entity path use them without
        # turning them into a semantic metadata filter or disabling speculation.
        scope_entities = {}
        if academic_scope and getattr(academic_scope, "programme_id", None):
            inferred_progs = self._scope_program_names(academic_scope)
            if inferred_progs:
                scope_entities["program_name"] = (
                    inferred_progs[0] if len(inferred_progs) == 1 else inferred_progs
                )

        # Submit the speculative retrieval call to executor. It runs the
        # semester-expanded query without query entities, while retaining the
        # student's programme only as a soft entity-path signal.
        query_speculative = self._expand_semesters(query)
        future_speculative = self.executor.submit(
            self._retrieve_dual_path,
            query_speculative,
            {"scope_entities": scope_entities},
            allowed_roles,
            academic_scope,
        )

        plan = future_plan.result()

        entities = plan.setdefault("entities", {})
        if scope_entities and not entities.get("program_name"):
            plan["scope_entities"] = scope_entities

        # Check if the plan contains anything that modifies retrieval or query
        has_entities = any(entities.get(k) for k in [
            "faculty_name", "event_name", "program_name", "department_name", 
            "scholarship_name", "course_code", "course_name", "semester", "rule_year"
        ])
        decomposed_queries = plan.get("query_decomposition")
        is_claim_verification = plan.get("is_claim_verification", False)
        requires_complete_list = plan.get("requires_complete_list", False)
        plan_required_sections = plan.get("retrieval_hints", {}).get("required_sections", [])
        expanded_terms = plan.get("expanded_terms", [])

        use_speculative = (
            not has_entities
            and not decomposed_queries
            and not is_claim_verification
            and not requires_complete_list
            and not plan_required_sections
            and not expanded_terms
        )

        retrieval_intent = plan.get("retrieval_intent", "general")

        # Abstain only for personal/"my programme" curriculum questions when we
        # cannot resolve the student's AcademicScope. If the user (or rewriter)
        # already named a programme/course, retrieve without personal scope —
        # curriculum docs are public and the named entity is enough to filter.
        # Fix EP-OVERRIDE (rag_detailed_report Aug 2026): also bypass when the
        # raw query explicitly names a programme abbreviation, year ordinal, or
        # semester number — these are always public timetable/curriculum queries.
        _explicit_prog_in_query = bool(
            RetrievalPipeline._EXPLICIT_PROGRAMME_IN_QUERY_RE.search(original_query or "")
        )
        if (
            user_role == "student"
            and self._requires_academic_scope(plan)
            and academic_scope is None
            and not self._has_explicit_programme_context(plan)
            and not _explicit_prog_in_query
        ):
            return {
                "query": original_query,
                "corrected_query": query,
                "plan": plan,
                "chunks": [],
                "context": "<context>\n</context>",
                "sources": [],
                "top_k_before_rerank": 0,
                "top_k_after_rerank": 0,
                "abstention_reason": "academic_scope_unavailable",
            }

        if use_speculative:
            logger.info("Speculative retrieval query matched; reusing speculative results.")
            results = future_speculative.result()
            corrected_query = query
        else:
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
            if is_claim_verification:
                query = query + " policy rule regulation verify"

            # Fix RP-FEE: replaces the old static FEE_KEYWORDS list. The retrieval
            # intent "admissions_information" combined with required_sections
            # already containing "Fee"/"Fees Structure"/"Tuition" (set generically
            # by the planner's few-shot examples, not by string-matching here) is
            # sufficient signal — no separate keyword list needed. We simply
            # surface the planner's own required_sections into the BM25 query
            # so its classification has retrieval-side effect.
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
            if expanded_terms:
                query = query + " " + " ".join(expanded_terms[:5])

            # Fix RP-COMPLETE: negation ("What is NOT X") and enumeration
            # ("how many total X") questions need the FULL set of relevant
            # chunks, not just the top-5 semantically closest ones — otherwise
            # the LLM only sees a partial list and cannot correctly identify
            # what is missing or excluded. Widen top_k generically using the
            # planner's requires_complete_list signal rather than hardcoding
            # per-entity-type retrieval counts.
            if requires_complete_list:
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

            # Retrieval filters are constructed inside _retrieve_dual_path (and,
            # for decomposed plans, per sub-query below) — not here. Building a
            # metadata_filter at this point would be dead code, and wiring it into
            # the dual path would wrongly entity-filter the semantic path, which is
            # deliberately entity-free. policy_version breadth (retrieving across
            # policy editions) comes from that entity-free semantic search plus the
            # reranker's policy_version section boosts, so no override is needed.

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

            # Fix #10: compute alias_resolved / top_k boost BEFORE the decomposed
            # branch so the same widened top_k applies to non-decomposed queries
            # entering _retrieve_dual_path. Previously this lived only inside the
            # decomposed block, so bare sentinel aliases ("mtech") got top_k=5
            # on non-decomposed paths — too narrow for an unfiltered index search.
            base_top_k = plan.get("top_k", 5)
            raw_program = plan.get("entities", {}).get("program_name", "")
            # Guard: program_name may be a list for multi-program queries; take the
            # first element for the alias-resolved / top_k heuristic only.
            if isinstance(raw_program, list):
                raw_program_scalar = raw_program[0] if raw_program else ""
            else:
                raw_program_scalar = raw_program
            canonical_program = self._canonical_program_name(raw_program_scalar) if raw_program_scalar else None
            alias_resolved = (
                canonical_program is not None
                and canonical_program not in self.BROAD_PROGRAM_SENTINELS
            )
            effective_top_k = base_top_k if alias_resolved else max(base_top_k, 15)
            # Write it back so _retrieve_dual_path and sub-query loops both see it.
            plan["top_k"] = effective_top_k

            if decomposed_queries:
                all_results = []

                # Fix #10: top_k already computed above (applies to both paths)
                retrieval_top_k = effective_top_k

                for subquery in decomposed_queries:
                    subquery_expanded = self._expand_semesters(subquery)

                    # Issue 2 fix: hard-filter this sub-query's candidate pool
                    # to recent document_year when the original query (not
                    # just this sub-query fragment) signals recency intent.
                    sub_recency_filter = self._recency_filter(plan, query)
                    sub_scatter_filter = self._scatter_gather_filter(plan, query)

                    sub_metadata_filter = self._combine_filters(
                        self._build_metadata_filter(plan, subquery_expanded),
                        sub_recency_filter,
                        sub_scatter_filter,
                        self._academic_scope_filter(academic_scope),
                    )
                    if allowed_roles:
                        auth_filter = {"authorization": {"$in": allowed_roles}}
                        sub_metadata_filter = self._combine_filters(sub_metadata_filter, auth_filter)

                    sub_results = (
                        self.retriever.retrieve(
                            query=subquery_expanded,
                            top_k=retrieval_top_k,
                            metadata_filter=sub_metadata_filter,
                            allowed_roles=allowed_roles
                        )
                    )

                    # Query entity filters may be relaxed only within the same
                    # role and academic scope. Applicability never broadens.
                    if not sub_results and sub_metadata_filter:
                        fallback_filter = self._combine_filters(
                            {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                            self._academic_scope_filter(academic_scope),
                        )
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
                    # also retry filter-free (preserving DLS) to maximise distinct coverage.
                    if sub_results and sub_metadata_filter:
                        already_seen_ids = {r["id"] for r in all_results}
                        new_in_sub = [r for r in sub_results if r["id"] not in already_seen_ids]
                        if len(new_in_sub) == 0:
                            # All sub-results already collected — retry without filter (preserving DLS)
                            fallback_filter = self._combine_filters(
                                {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                                self._academic_scope_filter(academic_scope),
                            )
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
                # Main query retrieval using dual path (returns 50-60 chunks)
                results = self._retrieve_dual_path(
                    query, plan, allowed_roles=allowed_roles, academic_scope=academic_scope
                )

        # ── Entity-based retrieval (professor's algorithm) ─────────────────
        # Merge entity-matched chunks (Step 2: Chunks→Triples→Entity) with
        # the vector/BM25 results into a unified chunk pool for reranking.
        # Fix RP1: previously two separate blocks existed — one guarded by
        # `not decomposed_queries` and a second unconditional one. For
        # non-decomposed queries both ran, injecting entity chunks twice
        # (before dedup). Collapsed into a single unconditional block so
        # entity retrieval runs exactly once for all query types.
        if self.entity_retriever:
            soft_entities = dict(plan.get("scope_entities") or {})
            soft_entities.update(entities)
            entity_chunks = (
                self.entity_retriever.retrieve_by_entities(
                    soft_entities,
                    allowed_roles=allowed_roles,
                    academic_scope=academic_scope,
                )
            )

            print("\n" + "=" * 80)
            print(f"ENTITY RETRIEVER RETURNED {len(entity_chunks)} CHUNKS")

            for idx, chunk in enumerate(entity_chunks[:20], start=1):
                meta = chunk.get("metadata", {})

                print(f"{idx:02d}.")
                print(f"Title      : {meta.get('title', 'N/A')}")
                print(f"Course Code: {meta.get('course_code', 'N/A')}")
                print(f"Program    : {meta.get('program_name', 'N/A')}")
                print(f"H1         : {meta.get('h1', 'N/A')}")
                print("-" * 60)

            print("=" * 80)

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

        results = self._eligible_results(deduped, academic_scope)

        # Diagnostic 4: Verify whether IE402 course policy exists anywhere in retrieval pool
        found_ie402 = []
        for cand in results:
            meta = cand.get("metadata", {}) if isinstance(cand, dict) else {}
            sf = str(meta.get("source_file") or meta.get("path") or meta.get("file") or "")
            t_val = str(meta.get("title") or "")
            h1_val = str(meta.get("h1") or "")
            if "IE402" in sf.upper() or "IE402" in t_val.upper() or "IE402" in h1_val.upper():
                found_ie402.append((cand, sf, t_val, h1_val))

        print("\n" + "=" * 80)
        if found_ie402:
            print("FOUND COURSE DOCUMENT:")
            for cand, sf, t_val, h1_val in found_ie402:
                meta = cand.get("metadata", {})
                print(f"ID          : {cand.get('id')}")
                print(f"Title       : {meta.get('title', 'N/A')}")
                print(f"Source File : {meta.get('source_file') or meta.get('path') or meta.get('file')}")
                print(f"H1          : {meta.get('h1', 'N/A')}")
                print(f"Course Code : {meta.get('course_code', 'N/A')}")
                print(f"Program     : {meta.get('program_name', 'N/A')}")
                print(f"Chunk Index : {meta.get('chunk_index', 'N/A')}")
                print("-" * 60)
        else:
            print("NO IE402 COURSE DOCUMENT FOUND IN RETRIEVAL POOL")
        print("=" * 80 + "\n")

        # Diagnostic 5: Log retrieval pool composition grouped by source file
        counts = {}
        for cand in results:
            meta = cand.get("metadata", {}) if isinstance(cand, dict) else {}
            sf = meta.get("source_file") or meta.get("path") or meta.get("file") or "Unknown"
            sf_name = os.path.basename(str(sf))
            counts[sf_name] = counts.get(sf_name, 0) + 1

        if "IE402.md" not in counts:
            counts["IE402.md"] = 0

        print("\n" + "=" * 80)
        print("RETRIEVAL POOL COMPOSITION BY SOURCE FILE")
        for src, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{src} : {count} chunks")
        print("=" * 80 + "\n")

        def _log_candidates(title_header, candidates):
            print("\n" + "=" * 80)
            print(title_header)
            print()
            top20 = candidates[:20] if candidates else []
            for idx, item in enumerate(top20, start=1):
                meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                cc = meta.get("course_code") or "N/A"
                t_val = meta.get("title") or "N/A"
                h1_val = meta.get("h1") or "N/A"
                s_val = item.get("fusion_score")
                if s_val is None:
                    s_val = item.get("rerank_score")
                if s_val is None:
                    s_val = item.get("score")
                if s_val is None:
                    s_val = item.get("cosine_score")
                if s_val is None:
                    s_val = 0.0
                print(f"{idx:02d}. Course: {cc}")
                print(f"    Title: {t_val}")
                print(f"    H1: {h1_val}")
                print(f"    Score: {float(s_val):.4f}")
                print()
            print("=" * 80)

        _log_candidates("RETRIEVAL RESULTS BEFORE RERANK", results)

        if decomposed_queries:
            # Fix A: run a final joint cross-encoder rerank over the merged
            # pool using the original user query (not a sub-query string).
            # Previously, sub-results were merged raw with no joint scoring,
            # so poorly-scored chunks from one sub-query could displace
            # high-quality chunks from another.
            #
            # Issue 1 fix #4: chunk-window expansion previously only ran on
            # the non-decomposed path below, so multi-part/comparison
            # queries never got adjacent-chunk context even when the real
            # answer for one leg of the comparison spanned two chunks.
            # Mirror the same two-stage expand+rerank here.
            stage1_reranked = (
                self.reranker.rerank(
                    query=original_query,
                    results=results,
                    plan=plan
                )
            )
            _log_candidates("FINAL RERANK", reranked)

            top_candidates = stage1_reranked[:12]
            expand_window = 2 if retrieval_intent == "policy_version" else 1
            expanded_candidates = self._eligible_results(
                self._expand_adjacent_chunks(top_candidates, window=expand_window), academic_scope
            )

            reranked = (
                self.reranker.rerank(
                    query=original_query,
                    results=expanded_candidates,
                    plan=plan
                )
            )

        else:
            # ── TWO-STAGE RERANKING ──
            # Stage 1: Fast rerank on unexpanded chunks
            stage1_reranked = self.reranker.rerank(
                query=query,
                results=results,
                plan=plan
            )
            _log_candidates("AFTER STAGE-1 RERANK", stage1_reranked)
            
            # Select top 18 candidates
            top_candidates = stage1_reranked[:18]
            
            # Expand only the top 18 candidates
            expand_window = 2 if retrieval_intent == "policy_version" else 1
            expanded_candidates = self._eligible_results(
                self._expand_adjacent_chunks(top_candidates, window=expand_window), academic_scope
            )
            
            # Stage 2: Final precise rerank on expanded top 18 chunks
            reranked = self.reranker.rerank(
                query=query,
                results=expanded_candidates,
                plan=plan
            )
            _log_candidates("FINAL RERANK", reranked)

        # Fix TK1: previously capped at min(plan["top_k"], 5) which destroyed
        # the multi-entity boost (num_entities*3 was always clamped back to 5).
        # For multi-entity queries 2 entities need at least 3 chunks each = 6.
        # Cap raised to 8 to give comparison queries enough chunks while staying
        # within the context token budget (3000 tokens ≈ 8-9 chunks).
        #
        # Fix TK2: this cap was silently undoing the requires_complete_list
        # top_k=12 boost set above — "which clubs does DAU have" and similar
        # enumeration queries got plan["top_k"]=12 but then
        # min(12, 5)=5 threw 7 of those chunks away before they ever reached
        # the LLM, producing partial lists (e.g. "top 10 clubs" out of 30+).
        # requires_complete_list queries now get the same higher ceiling as
        # multi_entity_query, and the effective context-token budget is
        # widened to match (see ContextBuilder.build's retrieval_intent
        # handling) so those extra chunks aren't cut again downstream.
        if requires_complete_list:
            max_final = 15
        elif plan.get("multi_entity_query"):
            max_final = 8
        else:
            max_final = 5
        final_top_k = min(plan.get("top_k", 5), max_final)

        # Fix C (source_match_analysis Root Cause 4): Apply title_hint boost.
        # When the original query contains an explicit document title like
        # "According to 'Director General', ..." we lift any chunks from that
        # exact document to the front of the reranked list before slicing.
        # This prevents a thematically similar but wrong document (e.g. the
        # Organogram page) from displacing the explicitly-named one when both
        # receive similar reranker scores.
        if title_hint:
            _hint_lower = title_hint.lower()
            _title_match = []
            _rest = []
            for chunk in reranked:
                doc_title = (
                    chunk.get("metadata", {}).get("title", "")
                    or chunk.get("metadata", {}).get("document_title", "")
                    or ""
                )
                if _hint_lower in doc_title.lower():
                    _title_match.append(chunk)
                else:
                    _rest.append(chunk)
            if _title_match:
                logger.debug(
                    "title_hint '%s' boosted %d chunk(s) to front of reranked list.",
                    title_hint,
                    len(_title_match),
                )
                reranked = _title_match + _rest

        final_chunks = reranked[:final_top_k]

        built = (
            self.builder.build(
                final_chunks,
                retrieval_intent=retrieval_intent,
                requires_complete_list=requires_complete_list,
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

            "citation_map":
                built.get("citation_map", {}),

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
        print("\n" + "=" * 60)
        print("===== ADJACENT CHUNK EXPANSION =====")
        for cand in candidates:
            metadata = cand.get("metadata", {})
            doc_id = metadata.get("document_id")
            chunk_idx = metadata.get("chunk_index")
            if not doc_id or chunk_idx is None:
                expanded_candidates.append(cand)
                continue

            chunk_idx = int(chunk_idx)
            parts = []
            added_adjacent = []

            # Collect preceding chunks within window
            for offset in range(window, 0, -1):
                prev_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx - offset))
                if prev_chunk:
                    parts.append(prev_chunk.get("text", ""))
                    added_adjacent.append(f"prev (-{offset}): {prev_chunk.get('chunk_id')}")

            parts.append(metadata.get("text", ""))

            # Collect following chunks within window
            for offset in range(1, window + 1):
                next_chunk = self.chunk_by_coordinate.get((doc_id, chunk_idx + offset))
                if next_chunk:
                    parts.append(next_chunk.get("text", ""))
                    added_adjacent.append(f"next (+{offset}): {next_chunk.get('chunk_id')}")

            expanded_text = "\n\n".join(filter(None, parts))

            new_cand = dict(cand)
            new_cand["metadata"] = dict(metadata)
            new_cand["metadata"]["text"] = expanded_text
            expanded_candidates.append(new_cand)

            print(f"Triggering Chunk: {cand.get('id')} ({metadata.get('title')})")
            if added_adjacent:
                print("   Added Neighbor Chunks: " + ", ".join(added_adjacent))
            else:
                print("   (No adjacent chunks found in store)")
        print("=" * 60)

        return expanded_candidates

    def _retrieve_dual_path(self, query, plan, allowed_roles=None, academic_scope=None, _skip_recency=False):
        """
        Runs dual-path retrieval: Entity Path (BM25 + Semantic fused via RRF) and
        Semantic Path (Top 50 cosine similarity). Norms both pools using Min-Max and
        combines them with an equal 50/50 weighted sum.
        """
        # Issue 2 fix: "latest"/"this semester"/... becomes a hard document_year
        # filter applied to both paths below, not just a reranker-side boost.
        recency_filter = None if _skip_recency else self._recency_filter(plan, query)
        if recency_filter:
            print("\n" + "=" * 60)
            print("===== RECENCY HARD FILTER =====")
            print(f"Query: {query!r} -> {recency_filter}")
            print("=" * 60)

        # 1. Entity Path
        entities = dict(plan.get("scope_entities") or {})
        entities.update(plan.get("entities", {}))
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
            combined_filter = self._combine_filters(
                ent_filter,
                recency_filter,
                {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                self._academic_scope_filter(academic_scope),
            )

            # Query retriever to get top 3 fused BM25 + dense chunks for this entity
            res_list = self.retriever.retrieve(
                query=ent_text,
                top_k=3,
                metadata_filter=combined_filter,
                allowed_roles=allowed_roles
            )
            if not res_list and ent_filter:
                # Relax the entity clause first but keep the recency hard
                # filter — only the outer retry (below, when the whole dual
                # path comes back empty) drops recency entirely.
                fallback_filter = self._combine_filters(
                    recency_filter,
                    {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                    self._academic_scope_filter(academic_scope),
                )
                res_list = self.retriever.retrieve(
                    query=ent_text,
                    top_k=3,
                    metadata_filter=fallback_filter,
                    allowed_roles=allowed_roles
                )
            
            for rank, res in enumerate(res_list, start=1):
                chunk_id = res["id"]
                if chunk_id not in entity_pool:
                    entity_pool[chunk_id] = {
                        "chunk": res,
                        "rrf_score": 0.0
                    }
                entity_pool[chunk_id]["rrf_score"] += 1.0 / (60.0 + rank)

        # Full-query lexical (BM25) pass. The per-entity loop above only runs
        # BM25 for planner-extracted entities, so a query that carries strong
        # keyword signal but yields no high-confidence entity (e.g. "what are
        # the hostel rules", "course policy of EL470") reached this pool empty
        # and fusion collapsed to pure dense search — which buries the exact
        # document under near-duplicate chunks. Running BM25 on the raw query
        # and folding it into the same RRF pool restores the lexical half of
        # hybrid retrieval for every query, not just entity queries. The same
        # authorization + academic-scope filter is applied so role/scope
        # gating is never bypassed.
        if getattr(self.retriever, "bm25", None):
            lexical_filter = self._combine_filters(
                {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                self._academic_scope_filter(academic_scope),
            )
            lexical_results = self.retriever.bm25.retrieve(
                query=query,
                top_k=20,
                metadata_filter=lexical_filter,
                allowed_roles=allowed_roles,
            )
            for rank, res in enumerate(lexical_results, start=1):
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

        # Diagnostic 2: Log raw BM25 / Entity results
        print("\n" + "=" * 80)
        print("===== RAW BM25 / ENTITY RESULTS (TOP 20) =====")
        if not entity_list:
            print("BM25 returned 0 documents.")
        else:
            for idx, item in enumerate(entity_list[:20], start=1):
                meta = item.get("metadata", {})
                src_file = meta.get("source_file") or meta.get("path") or meta.get("file") or "N/A"
                print(f"{idx:02d}. ID         : {item.get('id')}")
                print(f"    Score      : {item.get('entity_score', 0.0):.4f}")
                print(f"    Title      : {meta.get('title', 'N/A')}")
                print(f"    Source File: {src_file}")
                print(f"    H1         : {meta.get('h1', 'N/A')}")
                print(f"    Course Code: {meta.get('course_code', 'N/A')}")
                print(f"    Program    : {meta.get('program_name', 'N/A')}")
                print("-" * 40)
        print("=" * 80)

        # Min-Max normalize entity path scores
        if entity_list:
            scores = [c["entity_score"] for c in entity_list]
            min_val = min(scores)
            max_val = max(scores)
            val_range = max_val - min_val
            for c in entity_list:
                c["normalized_score"] = (c["entity_score"] - min_val) / val_range if val_range > 0 else 1.0

        # 2. Semantic Path: Top-50 vector search (using Pinecone/Qdrant index query directly)
        semantic_list = []
        if self.retriever.index is None:
            logger.info("Semantic retrieval disabled because the vector index is unavailable; continuing with entity-path results only.")
        else:
            try:
                query_embedding = self.retriever.embed_query(query)
                if query_embedding is None:
                    raise RuntimeError("Query embedding unavailable")
                
                entity_filter = self._build_metadata_filter(plan)
                
                print("\n" + "=" * 60)
                print("===== METADATA FILTER =====")
                if not entity_filter:
                    print("None")
                else:
                    def _parse(clause):
                        if not isinstance(clause, dict):
                            return
                        for k, v in clause.items():
                            if k == "$and" and isinstance(v, list):
                                for item in v:
                                    _parse(item)
                            elif not k.startswith("$"):
                                if isinstance(v, dict) and "$in" in v:
                                    val_str = ", ".join(str(x) for x in v["$in"])
                                    print(f"{k} = {val_str}")
                                elif isinstance(v, dict) and "$eq" in v:
                                    print(f"{k} = {v['$eq']}")
                                else:
                                    print(f"{k} = {v}")
                    _parse(entity_filter)
                print("=" * 60)

                scatter_filter = self._scatter_gather_filter(plan, query)

                semantic_filter = self._combine_filters(
                    entity_filter,
                    recency_filter,
                    scatter_filter,
                    {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                    self._academic_scope_filter(academic_scope),
                )
                results = self.retriever.index.query(
                    vector=query_embedding,
                    top_k=50,
                    include_metadata=True,
                    filter=semantic_filter
                )
                matches = list(results.get("matches", []))
                useful_matches = self._eligible_results(
                    [{"metadata": match.get("metadata", {})} for match in matches],
                    academic_scope,
                )
                minimum_useful = min(max(int(plan.get("top_k", 5)), 1), 5)
                if entity_filter and len(useful_matches) < minimum_useful:
                    fallback_filter = self._combine_filters(
                        {"authorization": {"$in": allowed_roles}} if allowed_roles else None,
                        self._academic_scope_filter(academic_scope),
                    )
                    fallback_results = self.retriever.index.query(
                        vector=query_embedding,
                        top_k=50,
                        include_metadata=True,
                        filter=fallback_filter,
                    )
                    seen_match_ids = {match.get("id") for match in matches}
                    matches.extend(
                        match
                        for match in fallback_results.get("matches", [])
                        if match.get("id") not in seen_match_ids
                    )

                for match in matches:
                    semantic_list.append({
                        "id": match["id"],
                        "score": match["score"],
                        "cosine_score": match["score"],
                        "metadata": match["metadata"],
                        "semantic_score": match["score"]
                    })
            except Exception as exc:
                logger.warning("Semantic retrieval failed; continuing without it: %s", exc)

        # Min-Max normalize semantic path scores
        if semantic_list:
            scores = [c["semantic_score"] for c in semantic_list]
            min_val = min(scores)
            max_val = max(scores)
            val_range = max_val - min_val
            for c in semantic_list:
                c["normalized_score"] = (c["semantic_score"] - min_val) / val_range if val_range > 0 else 1.0

        # Diagnostic 3 (Part A): Log RRF inputs before fusion
        print("\n" + "=" * 80)
        print(f"Dense candidates: {len(semantic_list)}")
        print(f"BM25 candidates: {len(entity_list)}")
        print("=" * 80)

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

        # Diagnostic 3 (Part B): Log RRF candidates after fusion
        print("\n" + "=" * 80)
        print(f"Merged candidates: {len(final_candidates)}")
        print("=" * 80 + "\n")

        # Sort candidates by final fusion score descending
        final_candidates.sort(key=lambda x: x["fusion_score"], reverse=True)
        eligible = self._eligible_results(final_candidates, academic_scope)

        # Issue 2 fix: the hard recency filter can legitimately zero out a
        # pool if year-tagging is incomplete for this document type. Rather
        # than surface "no results" to the user, retry once without it —
        # this is the ONLY point recency is dropped entirely; every filter
        # above this still preferred it first.
        if not eligible and recency_filter and not _skip_recency:
            logger.info(
                "Recency hard filter (%s) returned zero candidates for %r; retrying without it.",
                recency_filter, query,
            )
            return self._retrieve_dual_path(
                query, plan, allowed_roles=allowed_roles, academic_scope=academic_scope, _skip_recency=True
            )

        return eligible
