import json
import re

from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, metadata_path):

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.chunks = json.load(f)

        corpus = []

        for chunk in self.chunks:

            text = self._build_text(
                chunk
            )

            corpus.append(
                self._tokenize(text)
            )

        self.bm25 = BM25Okapi(
            corpus
        )

    def _build_text(
        self,
        chunk
    ):

        parts = [

            chunk.get(
                "faculty_name",
                ""
            ),

            chunk.get(
                "program_name",
                ""
            ),

            chunk.get(
                "event_name",
                ""
            ),

            chunk.get(
                "title",
                ""
            ),

            chunk.get(
                "h1",
                ""
            ),

            chunk.get(
                "h2",
                ""
            ),

            chunk.get(
                "h3",
                ""
            ),

            chunk.get(
                "text",
                ""
            ),
            
            chunk.get(
                "semester",
                ""
            ),

            chunk.get(
                "course_code",
                ""
            ),

            chunk.get(
                "course_name",
                ""
            ),

            chunk.get(
                "course_type",
                ""
            ),

            chunk.get(
                "credits",
                ""
            )

        ]

        return " ".join(
            str(x)
            for x in parts
            if x
        )
    
    STOPWORDS = {
        "what",
        "how",
        "does",
        "are",
        "the",
        "a",
        "an",
        "in",
        "of",
        "for",
        "to",
        "is",
        "on"
    }


    def _tokenize(
        self,
        text
    ):
        
        tokens = re.findall(
            r"[A-Za-z0-9_-]+",
            text.lower()
        )

        return [
            token
            for token in tokens
            if token not in self.STOPWORDS
        ]

    
    def _matches_filter(
        self,
        chunk,
        metadata_filter
    ):

        if not metadata_filter:
            return True

        if "$and" in metadata_filter:

            return all(

                self._matches_filter(
                    chunk,
                    condition
                )

                for condition in metadata_filter["$and"]

            )

        if "$or" in metadata_filter:

            return any(

                self._matches_filter(
                    chunk,
                    condition
                )

                for condition in metadata_filter["$or"]

            )

        for key, condition in metadata_filter.items():

            if isinstance(condition, dict):

                if "$eq" in condition:

                    if chunk.get(key) != condition["$eq"]:
                        return False

            else:

                if chunk.get(key) != condition:
                    return False

        return True


    def retrieve(
        self,
        query,
        top_k=10,
        metadata_filter=None
    ):

        query_tokens = (
            self._tokenize(query)
        )

        candidate_indices = []

        for idx, chunk in enumerate(self.chunks):

            if not self._matches_filter(
                chunk,
                metadata_filter
            ):
                continue

            candidate_indices.append(idx)

        scores = (
            self.bm25.get_scores(
                query_tokens
            )
        )

        ranked_indices = sorted(
            candidate_indices,
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []

        for idx in ranked_indices:

            results.append({

                "id":
                    self.chunks[idx][
                        "chunk_id"
                    ],

                "score":
                    float(scores[idx]),

                "metadata":
                    self.chunks[idx]
            })

        return results