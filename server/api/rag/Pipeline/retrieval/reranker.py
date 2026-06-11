class Reranker:

    H1_BOOST = 0.05
    H2_BOOST = 0.15
    H3_BOOST = 0.10

    INTENT_SECTION_MAP = {

        "research": [
            "research",
            "specialization",
            "publications"
        ],

        "contact": [
            "contact information",
            "website links"
        ],

        "overview": [
            "overview",
            "biography",
            "profile"
        ],

        "eligibility": [
            "eligibility",
            "admission process"
        ],

        "scholarship": [
            "scholarship",
            "financial assistance"
        ],

        "facilities": [
            "facilities",
            "infrastructure",
            "food court",
            "halls of residence"
        ],

        "event_details": [
            "event details",
            "venue",
            "organizers",
            "correspondence"
        ]
    }

    def rerank(
        self,
        results,
        plan
    ):

        intent = plan.get(
            "intent",
            "general"
        )

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

        intent_sections = (
            self.INTENT_SECTION_MAP.get(
                intent,
                []
            )
        )

        reranked = []

        for result in results:

            score = result["score"]

            metadata = result["metadata"]

            h1 = (
                metadata
                .get("h1") or ""
            ).lower()

            h2 = (
                metadata
                .get("h2") or ""
            ).lower()

            h3 = (
                metadata
                .get("h3") or ""
            ).lower()

            for section in boost_sections:

                section = section.lower()

                if section in h1:
                    score += self.H1_BOOST * 2

                if section in h2:
                    score += self.H2_BOOST

                if section in h3:
                    score += self.H3_BOOST

            for section in intent_sections:

                if section in h1:
                    score += self.H1_BOOST * 2

                if section in h2:
                    score += self.H2_BOOST

                if section in h3:
                    score += self.H3_BOOST

                    
            result["reranked_score"] = score

            reranked.append(result)

        reranked.sort(
            key=lambda x: x["reranked_score"],
            reverse=True
        )

        return reranked