import heapq
import json
import re

from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, metadata_path):
        self.metadata_path = metadata_path
        self.rebuild_index()

    def rebuild_index(self):
        with open(
            self.metadata_path,
            "r",
            encoding="utf-8"
        ) as f:

            chunks = json.load(f)

        corpus = []

        for chunk in chunks:

            text = self._build_text(
                chunk
            )

            corpus.append(
                self._tokenize(text)
            )

        self.chunks = chunks
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
    
    # Fix #12: expanded from 12 words to a comprehensive English stopword
    # list. Common query tokens like "which", "when", "where", "tell",
    # "about", "with" were previously polluting BM25 term frequencies.
    STOPWORDS = {
        # question words
        "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
        # articles / determiners
        "a", "an", "the", "this", "that", "these", "those",
        # prepositions
        "in", "of", "for", "to", "at", "by", "from", "with", "about",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "on", "up",
        # conjunctions
        "and", "or", "but", "so", "yet", "nor", "both", "either",
        # auxiliaries / copulas
        "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had", "do", "does", "did",
        "will", "would", "shall", "should", "may", "might", "must",
        "can", "could",
        # pronouns
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "he", "him", "his", "she", "her", "hers",
        "it", "its", "they", "them", "their", "theirs",
        # common filler verbs / adverbs
        "tell", "give", "show", "get", "let", "make", "know", "see",
        "also", "just", "very", "more", "all", "any", "some", "no",
        "not", "only", "same", "than", "then", "too", "own", "such",
        # misc
        "please", "like", "list", "need", "want", "find", "look",
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
        import os
        if os.getenv("DISABLE_DLS_FILTER", "false").lower() == "true" or os.getenv("DISABLE_PINECONE_DLS_FILTER", "false").lower() == "true":
            def strip_auth(f):
                if not isinstance(f, dict): return f
                nf = {}
                for k, v in f.items():
                    if k == "authorization": continue
                    elif k in ["$and", "$or"]:
                        nl = [strip_auth(x) for x in v]
                        nl = [x for x in nl if x]
                        if nl: nf[k] = nl
                    else:
                        nf[k] = v
                return nf
            metadata_filter = strip_auth(metadata_filter)

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

        if "$not" in metadata_filter:
            return not self._matches_filter(chunk, metadata_filter["$not"])

        import os

        for key, condition in metadata_filter.items():

            if key == "authorization" and os.environ.get("DISABLE_DLS_FILTER", "").lower() == "true":
                continue

            if isinstance(condition, dict):

                if "$eq" in condition:

                    if chunk.get(key) != condition["$eq"]:
                        return False

                # Fix BM1: $in operator was not handled. When the retrieval
                # pipeline builds a multi-value filter (e.g. two programs in a
                # comparison query), it uses {"program_name": {"$in": [v1, v2]}}.
                # BM25 previously fell through to the outer else branch and
                # compared the chunk's string value to the dict object → always
                # False → zero BM25 results for all multi-program queries.
                elif "$in" in condition:
                    val = chunk.get(key)
                    if isinstance(val, list):
                        # Array intersection: True if any element in val is in condition["$in"]
                        if not any(v in condition["$in"] for v in val):
                            return False
                    else:
                        if val not in condition["$in"]:
                            return False

                elif "$gte" in condition:
                    value = chunk.get(key)
                    if not isinstance(value, (int, float)) or value < condition["$gte"]:
                        return False

                elif "$lte" in condition:
                    value = chunk.get(key)
                    if not isinstance(value, (int, float)) or value > condition["$lte"]:
                        return False

            else:

                if chunk.get(key) != condition:
                    return False

        return True


    def retrieve(
        self,
        query,
        top_k=10,
        metadata_filter=None,
        allowed_roles=None
    ):

        query_tokens = (
            self._tokenize(query)
        )

        if metadata_filter:
            candidate_indices = [
                idx
                for idx, chunk in enumerate(self.chunks)
                if self._matches_filter(chunk, metadata_filter)
            ]
        else:
            # No filter → every chunk is a candidate; skip the per-chunk scan.
            candidate_indices = range(len(self.chunks))

        scores = (
            self.bm25.get_scores(
                query_tokens
            )
        )

        # nlargest is O(n log k) vs O(n log n) for a full sort, and matches
        # sorted(..., reverse=True)[:k] exactly (including tie order).
        ranked_indices = heapq.nlargest(
            top_k,
            candidate_indices,
            key=scores.__getitem__
        )

        results = []

        max_score = max(scores[i] for i in ranked_indices) if ranked_indices else 0.0

        for idx in ranked_indices:
            raw_score = float(scores[idx])
            norm_score = raw_score / max_score if max_score > 0.0 else 0.0

            results.append({

                "id":
                    self.chunks[idx][
                        "chunk_id"
                    ],

                "score":
                    norm_score,

                "metadata":
                    self.chunks[idx]
            })

        return results
