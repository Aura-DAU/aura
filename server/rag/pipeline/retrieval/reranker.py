from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)
import torch


class Reranker:

    def __init__(self):
        # Upgraded to BAAI/bge-reranker-v2-m3
        self.tokenizer = AutoTokenizer.from_pretrained(
            "BAAI/bge-reranker-v2-m3"
        )

        self.model = AutoModelForSequenceClassification.from_pretrained(
            "BAAI/bge-reranker-v2-m3"
        )

        self.model.eval()

    def rerank(
        self,
        query,
        results,
        plan=None
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

        with torch.no_grad():
            cross_scores = (
                self.model(
                    **inputs
                )
                .logits
                .squeeze(-1)
                .tolist()
            )

        if not isinstance(cross_scores, list):
            cross_scores = [cross_scores]

        reranked = []

        for result, cross_score in zip(
            results,
            cross_scores
        ):
            # Keeping it strictly focused on cross-encoder scoring without heuristic tag boosts
            result["cross_score"] = float(cross_score)
            result["reranked_score"] = float(cross_score)

            reranked.append(
                result
            )

        reranked.sort(
            key=lambda x:
                x["reranked_score"],
            reverse=True
        )

        # Restrict candidate list to the Top-5 chunks to protect LLM API rate limits
        return reranked[:5]