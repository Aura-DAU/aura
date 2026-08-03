import os
import math
import re
from datetime import datetime
from typing import Optional

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
        matches = re.findall(r"\b(20[1-3]\d)(?:[-\u2013/]\d{2,4})?\b", str(text))
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

    def _ensure_local_model(self):
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

            pairs.append(
                [query, text]
            )

        reranker_service_url = os.getenv("RERANKER_SERVICE_URL")
        cross_scores = None

        if reranker_service_url:
            try:
                import requests
                resp = requests.post(
                    f"{reranker_service_url.rstrip('/')}/rerank",
                    json={"pairs": pairs},
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "scores" in data:
                        cross_scores = data["scores"]
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Remote reranker service failed: %s. Falling back to local model.", e)

        if cross_scores is None:
            self._ensure_local_model()
            import torch
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                cross_scores = (
                    self.model(
                        **inputs
                    )
                    .logits
                    .squeeze(-1)
                    .tolist()
                )
                if isinstance(cross_scores, float):
                    cross_scores = [cross_scores]

        reranked = []

        boost_sections = (
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

        for result, cross_score in zip(
            results,
            cross_scores
        ):

            metadata = result["metadata"]

            section_type = metadata.get("section_type", "general")

            query_semester = entities.get(
                "semester"
            )

            if isinstance(query_semester, list):
                query_semester = (
                    query_semester[0]
                    if query_semester
                    else None
                )

            semester_penalty = 0.0

            if (
                section_type == "curriculum"
                and query_semester
            ):

                chunk_semester = metadata.get(
                    "semester"
                )

                if (
                    chunk_semester
                    and chunk_semester != query_semester
                ):
                    # Fix #13: use a proportional penalty (10 % reduction of
                    # the normalised cross-score) instead of a hard -0.20 that
                    # is negligible at high logit values (e.g. +5.0 → +4.80).
                    semester_penalty = -0.10  # applied to the normalised score

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

            # Fix #4 / Fix RR-RECENCY: all components on comparable scales
            # [0, 1]. recency_boost's weight raised 0.05 → 0.15 (taken from
            # dense_score, 0.15 → 0.05) so that among documents the
            # cross-encoder scores as similarly relevant — which is exactly
            # what happens across several yearly versions of the same roster
            # — the newest one reliably wins instead of the tie effectively
            # being broken by noise.
            answerability_boost = 0.0
            lookup_keywords = [
                "who", "who is", "name", "convener", "convenor", "coordinator",
                "faculty advisor", "faculty adviser", "advisor", "mentor", "chair",
                "chairperson", "contact", "contact information", "email", "email id",
                "phone", "phone number", "mobile", "mobile number", "student id",
                "erp", "credits", "credit", "credit structure", "prerequisite",
                "prerequisites", "fee", "fees", "fee structure", "duration",
                "office", "policy", "syllabus"
            ]
            structured_fields = {
                "convener", "convenor", "coordinator", "faculty advisor", "faculty adviser",
                "advisor", "mentor", "chair", "chairperson", "student id", "erp",
                "email", "phone", "mobile", "contact", "credits", "credit",
                "prerequisite", "fee", "fees", "duration", "office", "policy", "syllabus"
            }
            query_lower = query.lower()
            keyword_pattern = r"\b(" + "|".join(re.escape(k) for k in lookup_keywords) + r")\b"
            if re.search(keyword_pattern, query_lower):
                chunk_full_text = "\n".join(
                    filter(
                        None,
                        [
                            metadata.get("title"),
                            metadata.get("category"),
                            metadata.get("cluster"),
                            metadata.get("h1"),
                            metadata.get("h2"),
                            metadata.get("h3"),
                            metadata.get("text"),
                        ]
                    )
                ).lower()
                if any(field in chunk_full_text for field in structured_fields):
                    answerability_boost = 1.0

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
                (0.15 * temporal_boost)
                +
                (0.05 * answerability_boost)
                +
                (semester_penalty * norm_cross)
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

        print("\n" + "=" * 60)
        print("===== CROSS-ENCODER RERANK RESULTS =====")
        print(f"Query: {query}")
        for rank, item in enumerate(reranked, start=1):
            meta = item.get("metadata", {})
            h_str = " / ".join(filter(None, [meta.get("h1"), meta.get("h2"), meta.get("h3")]))
            print(f"{rank}. reranked_score={item.get('reranked_score', 0.0):.4f} (cross_logit={item.get('cross_score', 0.0):.4f}) | chunk={item.get('id')}")
            print(f"   title={meta.get('title', 'N/A')}")
            print(f"   file={meta.get('source_file') or meta.get('relative_path', 'N/A')}")
            if h_str:
                print(f"   headers={h_str}")
        print("=" * 60)

        return reranked
