from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)

import torch


class Reranker:

    def __init__(self):

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                "BAAI/bge-reranker-base"
            )
        )

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                "BAAI/bge-reranker-base"
            )
        )

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

            text = metadata.get(
                "text",
                ""
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

        for result, cross_score in zip(
            results,
            cross_scores
        ):

            metadata = result["metadata"]

            section_type = metadata.get("section_type", "general")

            h1 = (
                metadata
                .get("h1", "")
                .lower()
            )

            h2 = (
                metadata
                .get("h2", "")
                .lower()
            )

            h3 = (
                metadata
                .get("h3", "")
                .lower()
            )

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

            dense_score = (
                result.get(
                    "score",
                    0
                )
            )

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

            target_section = (
                plan.get(
                    "retrieval_hints",
                    {}
                )
                .get(
                    "preferred_section_type"
                )
            )

            if target_section and section_type == target_section:
                section_boost += 0.25


            final_score = (
                (0.72 * float(cross_score))
                +
                (0.10 * dense_score)
                +
                (0.05 * metadata_boost)
                +
                (0.05 * required_section_boost)
                +
                (0.08 * section_boost)
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