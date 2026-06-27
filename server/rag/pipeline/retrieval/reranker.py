import os
import math
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


class Reranker:

    def __init__(self):
        env_device = os.getenv("RERANKER_DEVICE")
        if env_device:
            self.device = torch.device(env_device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                "BAAI/bge-reranker-v2-m3"
            )
        )

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                "BAAI/bge-reranker-v2-m3"
            )
        ).to(self.device)

        self.model.eval()

        self.H1_BOOST = 0.10
        self.H2_BOOST = 0.20
        self.H3_BOOST = 0.15

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
                "how to apply"
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


            # Fix #4: all components are now on comparable scales [0, 1].
            # course_match_boost is weighted at 0.20 (was a raw +0.35 add).
            # semester_penalty is applied to the normalised cross component.
            final_score = (
                (0.65 * norm_cross)
                +
                (0.15 * dense_score)
                +
                (0.05 * metadata_boost)
                +
                (0.05 * required_section_boost)
                +
                (0.05 * section_boost)
                +
                (0.05 * course_match_boost)
                +
                # Fix #13: penalty is now a fraction of the normalised cross
                # score so it remains meaningful even at high relevance.
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

        return reranked
