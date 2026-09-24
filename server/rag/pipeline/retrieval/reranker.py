import os
import math
import re
import time
import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Remote-first reranking: a 503 from node4's concurrency gate (or a transient
# connection blip) usually clears within a second, so retry briefly before
# paying for the local fallback — bge-reranker-v2-m3 on CPU takes 15-40s per
# pool vs <1s on the remote GPU service.
RERANKER_REMOTE_ATTEMPTS = max(1, int(os.getenv("RERANKER_REMOTE_ATTEMPTS", "3")))
RERANKER_REMOTE_BACKOFF_S = max(0.0, float(os.getenv("RERANKER_REMOTE_BACKOFF_S", "0.5")))
# Local-fallback mini-batch size: one giant padded batch over the whole pool
# makes every pair pay the longest pair's token length and spikes memory.
RERANKER_LOCAL_BATCH_SIZE = max(1, int(os.getenv("RERANKER_LOCAL_BATCH_SIZE", "8")))

# Fix LOAD-1 (mirrors retriever.py): the remote-reranker call used a bare
# `requests.post` per call — a fresh TCP(+TLS) handshake every rerank. One
# process-wide pooled Session keeps sockets warm across calls, which matters
# more now that a compound message reranks once per sub-question in
# parallel. max_retries stays 0 on the adapter: pool the socket only, and
# leave the existing RERANKER_REMOTE_ATTEMPTS loop as the single retry layer.
RERANKER_HTTP_POOL_SIZE = max(1, int(os.getenv("RERANKER_HTTP_POOL_SIZE", "32")))
_rerank_session_lock = threading.Lock()
_rerank_session = None


def _get_rerank_session():
    global _rerank_session
    if _rerank_session is None:
        with _rerank_session_lock:
            if _rerank_session is None:
                import requests
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=RERANKER_HTTP_POOL_SIZE,
                    pool_maxsize=RERANKER_HTTP_POOL_SIZE,
                )
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                _rerank_session = session
    return _rerank_session

_ROMAN_OR_WORD_SEM = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8,
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
}
_SEM_TOKEN_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\b|"
    r"\b(viii|vii|vi|iv|iii|ii|v|i|first|second|third|fourth|fifth|sixth|seventh|eighth)\b"
)


def semester_numbers(value) -> set:
    """Normalise any semester spelling to a set of ints.

    The planner emits ints (3) while chunk metadata stores roman numerals
    ("III"); comparing them with != made the wrong-semester penalty fire on
    every curriculum chunk, i.e. it never discriminated. Accepts "III",
    "Semester 3", "3rd sem", 3, or a list of those.
    """
    items = value if isinstance(value, (list, tuple, set)) else [value]
    found = set()
    for item in items:
        if item is None or item == "":
            continue
        if isinstance(item, int) and not isinstance(item, bool):
            if 1 <= item <= 12:
                found.add(item)
            continue
        text = re.sub(r"\b(?:semester|sem)\b\.?", " ", str(item).lower())
        for num, word in _SEM_TOKEN_RE.findall(text):
            n = int(num) if num else _ROMAN_OR_WORD_SEM.get(word)
            if n and 1 <= n <= 12:
                found.add(n)
    return found

def extract_latest_year(metadata: dict) -> Optional[int]:
    """Extract a document's version year from its authoritative metadata.

    Extraction priority order:
    academic_year -> title -> h1 -> h2 -> h3 -> source_file -> relative_path -> document_year (LAST fallback)
    """
    texts_to_search = [
        metadata.get("academic_year", ""),
        metadata.get("title", ""),
        metadata.get("h1", ""),
        metadata.get("h2", ""),
        metadata.get("h3", ""),
        metadata.get("source_file", ""),
        metadata.get("relative_path", ""),
        metadata.get("document_year", ""),
    ]

    for text in texts_to_search:
        if not text:
            continue
        # Fix YEAR-UB1 (same bug as ingestion's resolve_document_academic_year):
        # \b treats "_" as a word character, so a \b-bounded year regex never
        # matches years embedded in snake_case source_file/relative_path
        # values like "..._autumn_2025_page_7.md" — this silently skipped
        # straight to document_year (a much weaker signal) for the majority
        # of this corpus's filenames. Digit-adjacency lookaround still
        # rejects non-year digit runs (e.g. "42025" or "20255").
        matches = re.findall(r"(?<!\d)(20[1-3]\d)(?:[-\u2013/]\d{2,4})?(?!\d)", str(text))
        if matches:
            return max(int(m) for m in matches)
    return None


class Reranker:

    def __init__(self):
        self.device = None
        self.tokenizer = None
        self.model = None
        self.H1_BOOST = 0.10
        self.H2_BOOST = 0.20
        self.H3_BOOST = 0.15
        # Prefer remote RERANKER_SERVICE_URL; only load the local cross-encoder
        # eagerly when no remote is configured (lazy fallback still happens in rerank).
        if not (os.getenv("RERANKER_SERVICE_URL") or "").strip():
            self._ensure_local_model()

    # Fix LOAD-2 (mirrors retriever.py): unlocked lazy load. A burst of
    # concurrent rerank() calls arriving while the remote reranker is down
    # (the only time this runs when RERANKER_SERVICE_URL is set) would each
    # pass the `is None` check before any finished, racing to construct
    # several copies of bge-reranker-v2-m3 at once — exactly when the system
    # is already most stressed. Double-checked locking, same pattern as
    # api/deps.py::get_aura(): the fast (already-loaded) path never blocks.
    _local_model_lock = threading.Lock()

    def _ensure_local_model(self):
        if self.model is not None and self.tokenizer is not None:
            return
        with self._local_model_lock:
            if self.model is not None and self.tokenizer is not None:
                return

            import torch
            from transformers import (
                AutoTokenizer,
                AutoModelForSequenceClassification
            )

            env_device = os.getenv("RERANKER_DEVICE")
            if env_device:
                self.device = torch.device(env_device)
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")

            self.tokenizer = AutoTokenizer.from_pretrained(
                "BAAI/bge-reranker-v2-m3"
            )
            self.model = (
                AutoModelForSequenceClassification
                .from_pretrained("BAAI/bge-reranker-v2-m3")
            ).to(self.device)
            self.model.eval()

    # Matches a trailing "(Qualifier)" or a dash-separated short capitalized
    # tail, e.g. "Dean (Students)", "Hall of Residence (Men)",
    # "Executive Assistant – Dean (AP)" (paren wins if both are present).
    _QUALIFIER_RE = re.compile(
        r"\(([^)]{1,40})\)|[-\u2013]\s*([A-Z][A-Za-z .]{1,40})$"
    )

    @classmethod
    def _extract_qualifier(cls, label: str):
        label = (label or "").strip()
        if not label:
            return None, None
        m = cls._QUALIFIER_RE.search(label)
        if not m:
            return None, None
        qualifier = (m.group(1) or m.group(2) or "").strip().lower()
        base = (label[: m.start()] + label[m.end():]).strip(" -\u2013").lower()
        if not qualifier or not base:
            return None, None
        return base, qualifier

    @staticmethod
    def _qualifier_matches_query(qualifier: str, query_lower: str) -> bool:
        if not qualifier:
            return False
        if qualifier in query_lower:
            return True
        for word in re.findall(r"[a-z]{2,}", qualifier):
            if re.search(rf"\b{re.escape(word)}\b", query_lower):
                return True
        return False

    def _build_entity_adjustments(self, query, results):
        """Group candidates sharing a base label with differing qualifiers,
        and — only when the query names exactly one qualifier in a group —
        return {result_id: +0.20/-0.20} boosting the match and penalizing
        the rest of that group. Groups the query doesn't disambiguate (zero
        or 2+ qualifiers named) are left alone (no adjustment)."""

        groups: dict[str, dict[str, list]] = {}
        for r in results:
            metadata = r.get("metadata", {}) or {}
            label = (
                metadata.get("h3")
                or metadata.get("h2")
                or metadata.get("h1")
                or metadata.get("title")
                or ""
            )
            base, qualifier = self._extract_qualifier(label)
            if base is None:
                continue
            rid = r.get("id")
            if rid is None:
                continue
            groups.setdefault(base, {}).setdefault(qualifier, []).append(rid)

        query_lower = query.lower()
        adjustment: dict = {}
        for base, qualifier_map in groups.items():
            if len(qualifier_map) < 2:
                continue  # no ambiguity for this base entity in this pool
            matched = [
                q for q in qualifier_map
                if self._qualifier_matches_query(q, query_lower)
            ]
            if len(matched) != 1:
                continue  # query doesn't disambiguate, or names several
            winner = matched[0]
            for q, ids in qualifier_map.items():
                adj = 0.20 if q == winner else -0.20
                for rid in ids:
                    adjustment[rid] = adj
        return adjustment

    def rerank(

        self,
        query,
        results,
        plan
    ):

        if not results:
            return []

        pairs = []

        for result in results:

            metadata = result["metadata"]

            text = "\n".join(
                filter(
                    None,
                    [
                        metadata.get("title"),
                        metadata.get("category"),
                        metadata.get("cluster"),
                        metadata.get("h1"),
                        metadata.get("h2"),
                        metadata.get("h3"),
                        metadata.get("text")
                    ]
                )
            )

            MAX_RERANK_CHARS = 1600 # Approx 400 tokens
            if len(text) > MAX_RERANK_CHARS:
                text = text[:MAX_RERANK_CHARS]

            pairs.append(
                [query, text]
            )

        reranker_service_url = os.getenv("RERANKER_SERVICE_URL")
        cross_scores = None

        if reranker_service_url:
            session = _get_rerank_session()
            for attempt in range(1, RERANKER_REMOTE_ATTEMPTS + 1):
                try:
                    resp = session.post(
                        f"{reranker_service_url.rstrip('/')}/rerank",
                        json={"pairs": pairs},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if "scores" in data:
                            cross_scores = data["scores"]
                        break
                    if resp.status_code != 503:
                        # Non-503 failures (validation, model not loaded)
                        # won't heal on retry — fall back to local right away.
                        logger.warning(
                            "Remote reranker service returned HTTP %s. Falling back to local model.",
                            resp.status_code,
                        )
                        break
                    logger.warning(
                        "Remote reranker service busy (503), attempt %d/%d.",
                        attempt, RERANKER_REMOTE_ATTEMPTS,
                    )
                except Exception as e:
                    logger.warning(
                        "Remote reranker service failed (attempt %d/%d): %s",
                        attempt, RERANKER_REMOTE_ATTEMPTS, e,
                    )
                if attempt < RERANKER_REMOTE_ATTEMPTS:
                    time.sleep(RERANKER_REMOTE_BACKOFF_S)
            if cross_scores is None:
                logger.warning("Remote reranker service unavailable after %d attempt(s). Falling back to local model.", RERANKER_REMOTE_ATTEMPTS)

        if cross_scores is None:
            self._ensure_local_model()
            import torch
            # Mini-batched forward pass (RERANKER_LOCAL_BATCH_SIZE): running
            # the whole 60-90 pair pool as ONE padded batch made every pair
            # pay the longest pair's length and dominated CPU-fallback
            # latency. Batches are processed in input order and scores are
            # concatenated, so score order still matches the input pairs.
            cross_scores = []
            for batch_start in range(0, len(pairs), RERANKER_LOCAL_BATCH_SIZE):
                batch_pairs = pairs[batch_start:batch_start + RERANKER_LOCAL_BATCH_SIZE]
                inputs = self.tokenizer(
                    batch_pairs,
                    padding=True,
                    truncation=True,
                    # Issue 1 fix #1: chunks are 256 tokens, but stage-2 adjacent-
                    # chunk expansion (_expand_adjacent_chunks) concatenates up to
                    # 5 neighboring chunks (up to ~1280 tokens) before this text
                    # reaches the reranker. 512 was silently truncating the
                    # "next" chunk(s) off expanded candidates — exactly defeating
                    # the point of window expansion. BAAI recommends max_length
                    # =1024 for bge-reranker-v2-m3 (model supports up to 8192,
                    # but was fine-tuned at 1024).
                    max_length=1024,
                    return_tensors="pt"
                )

                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    batch_scores = (
                        self.model(
                            **inputs
                        )
                        .logits
                        .squeeze(-1)
                        .tolist()
                    )
                    if isinstance(batch_scores, float):
                        batch_scores = [batch_scores]
                cross_scores.extend(batch_scores)

        reranked = []

        # Copied: extending the plan's own list would grow it on every call.
        boost_sections = list(
            plan
            .get(
                "retrieval_hints",
                {}
            )
            .get(
                "boost_sections",
                []
            )
        )

        required_sections = (
            plan
            .get(
                "retrieval_hints",
                {}
            )
            .get(
                "required_sections",
                []
            )
        )

        retrieval_intent = (
            plan.get(
                "retrieval_intent",
                "general"
            )
        )

        if isinstance(
            retrieval_intent,
            list
        ):
            retrieval_intent = (
                retrieval_intent[0]
                if retrieval_intent
                else "general"
            )

        intent_boosts = {
            "faculty_profile": [
                "biography",
                "overview",
                "research",
                "teaching",
                "specialization"
            ],

            "faculty_research": [
                "research",
                "research interests",
                "publications"
            ],

            "faculty_contact": [
                "contact",
                "contact information"
            ],

            "program_overview": [
                "overview",
                "program overview",
                "about the program"
            ],

            "program_eligibility": [
                "eligibility",
                "eligibility criteria",
                "admission requirements"
            ],

            "program_curriculum": [
                "curriculum",
                "courses",
                "course structure"
            ],

            "admissions_information": [
                "admissions",
                "application process",
                "how to apply",
                # Fix RR1: fee-related heading keywords were missing, so the
                # reranker never boosted fee chunks for admissions queries.
                "fees structure",
                "fee structure",
                "tuition fee",
                "fee"
            ],

            "scholarship_information": [
                "scholarships",
                "financial aid",
                "awards"
            ],

            "event_information": [
                "event",
                "schedule",
                "details"
            ],

            # Fix RR2: version-history section headings boosted for policy_version intent.
            "policy_version": [
                "version history",
                "supersedes",
                "effective date",
                "revision",
                "amendment",
                "replaces"
            ],

            # Fix RR3: rules intent boosts regulation/conduct/malpractice headings.
            # Addresses Vedant report where course policy chunks outranked actual
            # academic regulation chunks for rules-intent queries.
            "rules": [
                "regulations",
                "rules",
                "malpractices",
                "code of conduct",
                "guidelines",
                "academic policy",
                "disciplinary",
                "examination policy"
            ],

            # Fix RR4: event_version intent boosts edition/schedule headings.
            # Addresses Events report where old convocation data overrode current.
            "event_version": [
                "convocation",
                "annual",
                "edition",
                "schedule",
                "graduates",
                "ceremony"
            ]
        }

        boost_sections.extend(
            intent_boosts.get(
                retrieval_intent,
                []
            )
        )

        boost_sections = list(
            set(boost_sections)
        )

        entities = plan.get(
            "entities",
            {}
        )

        target_section = (
            plan.get(
                "retrieval_hints",
                {}
            )
            .get(
                "preferred_section_type"
            )
        )

        explicit_rule_year = entities.get("rule_year")
        current_year = datetime.now().year
        # Recency decides the ranking only when the question is about the
        # latest/current version of something. Otherwise it is a small
        # tie-breaker between near-identical yearly versions, so a recent
        # notice cannot outrank the undated policy that answers the question.
        temporal_weight = 0.15 if plan.get("temporal_intent") else 0.03

        # ── Generic entity/qualifier disambiguation ─────────────────────
        # DAU's corpus is full of near-duplicate structured entries that
        # share a base role/office name but differ by a bracketed or
        # dash-suffixed qualifier: "Dean (Students)" vs "Dean (Academic
        # Programs)", "Hall of Residence (Men)" vs "(Women)", "Convener" vs
        # "Deputy Convener", etc. The cross-encoder alone often can't
        # separate these — same structure, same keywords, one differing
        # word — and once only a handful of chunks survive the token
        # budget (see AURA_MAX_CONTEXT_TOKENS in token_budget.py), whichever
        # lookalike ranks a hair higher can be the wrong one, with the model
        # then mislabeling it as whichever entity the user actually asked
        # about (this is what happened with the Dean Students/AP mix-up).
        #
        # Rather than hardcode specific office/role names, we extract a
        # "qualifier" from each candidate's own title/h1/h2/h3 — anything in
        # parentheses, or a short capitalized phrase after a trailing
        # " - "/" – " — group candidates that share the same base text with
        # the qualifier stripped, and only when the query names exactly one
        # qualifier within that group do we boost the matching chunk and
        # penalize the rest. If the query is ambiguous (names none or more
        # than one) we leave the group untouched so multi-entity comparison
        # queries aren't penalized.
        entity_adjustment = self._build_entity_adjustments(query, results)

        for result, cross_score in zip(
            results,
            cross_scores
        ):

            metadata = result["metadata"]

            section_type = metadata.get("section_type", "general")

            query_semesters = semester_numbers(entities.get("semester"))

            semester_penalty = 0.0

            if (
                section_type == "curriculum"
                and query_semesters
            ):

                chunk_semester = metadata.get(
                    "semester"
                )

                chunk_semesters = semester_numbers(chunk_semester)
                if (
                    chunk_semesters
                    and query_semesters.isdisjoint(chunk_semesters)
                ):
                    # Fix #13: use a proportional penalty (10 % reduction of
                    # the normalised cross-score) instead of a hard -0.20 that
                    # is negligible at high logit values (e.g. +5.0 → +4.80).
                    semester_penalty = -0.10  # applied to the normalised score

            # Generic entity/qualifier disambiguation (replaces the earlier
            # DEAN-CONFUSION hardcode — see _build_entity_adjustments above
            # for how this is computed once per candidate pool). Applies to
            # any "Base (Qualifier)" pair in the pool, not just Dean offices.
            entity_penalty = entity_adjustment.get(result.get("id"), 0.0)

            course_match_boost = 0.0

            query_course = entities.get(
                "course_code"
            )

            if isinstance(query_course, list):
                query_course = (
                    query_course[0]
                    if query_course
                    else None
                )

            if query_course:

                if metadata.get(
                    "course_code"
                ) == query_course:

                    # Fix #4: course_match_boost is now used as a weighted
                    # component (coefficient 0.20) rather than a raw add of
                    # 0.35, which previously inflated poorly-relevant chunks.
                    course_match_boost = 1.0  # normalised; weight applied below

            h1 = str(
                metadata.get("h1") or ""
            ).lower()


            h2 = str(
                metadata.get("h2") or ""
            ).lower()


            h3 = str(
                metadata.get("h3") or ""
            ).lower()


            metadata_boost = 0.0

            for section in boost_sections:

                section = section.lower()

                if section in h1:
                    metadata_boost += (
                        self.H1_BOOST
                    )

                if section in h2:
                    metadata_boost += (
                        self.H2_BOOST
                    )

                if section in h3:
                    metadata_boost += (
                        self.H3_BOOST
                    )

            # Fix #4: sigmoid-normalize the cross-encoder logit to [0, 1]
            # so it is on the same scale as all other components.  Previously
            # the raw logit (range -∞ to +∞) dominated the formula while the
            # dense_score contribution (RRF value × 0.10 ≈ 0.002) was noise.
            norm_cross = 1.0 / (1.0 + math.exp(-float(cross_score)))

            # Fix #4: scale the RRF/cosine dense score.  RRF values top out at
            # ~0.033 so the old 0.10 weight was effectively zero (≈ 0.003).
            # Use the cosine_score if available (range 0–1), else rrf_score.
            raw_dense = result.get("cosine_score") or result.get("rrf_score") or result.get("score") or 0.0
            # Clamp cosine/rrf to [0, 1]
            norm_dense = max(0.0, min(float(raw_dense), 1.0))

            dense_score = norm_dense

            required_section_boost = 0.0

            for section in required_sections:

                section = section.lower()

                if section in h1:
                    required_section_boost += 0.40

                if section in h2:
                    required_section_boost += 0.60

                if section in h3:
                    required_section_boost += 0.50


            section_boost = 0.0

            if target_section and section_type == target_section:
                section_boost += 0.25


            # Fix #12: cap variable boost components to [0.0, 1.0] so the
            # weighted sum stays on a consistent scale. Without this, multiple
            # matching sections can accumulate metadata_boost > 1.0, inflating
            # final scores beyond the intended [0, 1] range and making them
            # incomparable across queries.
            metadata_boost = min(metadata_boost, 1.0)
            required_section_boost = min(required_section_boost, 1.0)
            section_boost = min(section_boost, 1.0)
            course_match_boost = min(course_match_boost, 1.0)

            temporal_boost = 0.0
            if not explicit_rule_year:
                doc_year = extract_latest_year(metadata)
                if doc_year:
                    diff = current_year - doc_year
                    if diff <= 0:
                        temporal_boost = 1.0
                    elif diff <= 5:
                        temporal_boost = max(0.0, 1.0 - (diff * 0.2))
                else:
                    year_text = " ".join(
                        str(metadata.get(k) or "")
                        for k in ("academic_year", "title", "source_file", "relative_path")
                    )
                    year_match = re.search(
                        r"(?:20)?(\d{2})[_\-\u2013](\d{2})(?!\d)",
                        year_text,
                    )
                    bare_year_match = re.search(r"(20\d{2})(?!\d)", year_text)
                    if year_match:
                        start_yy = int(year_match.group(1))
                        end_yy = int(year_match.group(2))
                        if end_yy == (start_yy + 1) % 100 or end_yy == start_yy + 1:
                            temporal_boost = min(max((2000 + start_yy - 2020) / 10.0, 0.0), 1.0)
                    elif bare_year_match:
                        # No "YY-YY" academic-year pattern, but a plain 4-digit
                        # year is present (e.g. "Winter 2026") — still a genuine
                        # recency signal, just a different phrasing.
                        yyyy = int(bare_year_match.group(1))
                        temporal_boost = min(max((yyyy - 2020) / 10.0, 0.0), 1.0)
                    elif str(metadata.get("title") or "").lower().find("c_dcs") >= 0:
                        temporal_boost = 0.6

            # All components are on comparable [0, 1] scales.
            final_score = (
                (0.60 * norm_cross)
                +
                (0.05 * dense_score)
                +
                (0.05 * metadata_boost)
                +
                (0.05 * required_section_boost)
                +
                (0.05 * section_boost)
                +
                (0.05 * course_match_boost)
                +
                (temporal_weight * temporal_boost)
                +
                (semester_penalty * norm_cross)
                +
                entity_penalty
            )

            result[
                "cross_score"
            ] = float(
                cross_score
            )

            result[
                "reranked_score"
            ] = final_score

            reranked.append(
                result
            )

        reranked.sort(
            key=lambda x:
                x["reranked_score"],
            reverse=True
        )

        if logger.isEnabledFor(logging.DEBUG):
            for rank, item in enumerate(reranked[:10], start=1):
                logger.debug(
                    "rerank %d score=%.4f logit=%.4f chunk=%s title=%r",
                    rank,
                    item.get("reranked_score", 0.0),
                    item.get("cross_score", 0.0),
                    item.get("id"),
                    item.get("metadata", {}).get("title"),
                )

        return reranked