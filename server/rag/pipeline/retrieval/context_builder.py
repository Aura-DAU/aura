class ContextBuilder:

    # Fix G (original): cap context to avoid LLM truncation.
    # Fix Bug4: raised from 2000 → 3000 tokens. The original 2000-token cap
    # was too tight: a BS-MS admissions page has a long eligibility section
    # before the Fees Structure, so the fee chunk (chunk #3-4) was being
    # silently dropped when added after the eligibility chunks already consumed
    # ~1800 tokens. 3000 gives headroom for fee + scholarship + other data
    # while staying well under model context limits (system prompt ~450 +
    # history ~500 + 3000 context = ~3950 tokens, safe for all hosted models).
    MAX_CONTEXT_TOKENS = 3000

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: word count × 1.3 (accounts for sub-word splits)."""
        return int(len(text.split()) * 1.3)

    def build(self, chunks):

        documents = []

        sources = []
        seen_urls = set()

        context_tokens_used = 0

        for idx, chunk in enumerate(
            chunks,
            start=1
        ):

            metadata = chunk["metadata"]

            # Build the XML attributes string for the token estimate
            xml_attrs = (
                f'title="{metadata.get("title", "")}" '
                f'h1="{metadata.get("h1", "")}" '
                f'h2="{metadata.get("h2", "")}"'
            )
            chunk_text = metadata.get("text", "")
            estimated_tokens = self._estimate_tokens(xml_attrs + " " + chunk_text)

            # Fix G: enforce token budget — skip lower-ranked chunks that
            # would push us over the limit.
            if context_tokens_used + estimated_tokens > self.MAX_CONTEXT_TOKENS and idx > 1:
                break

            context_tokens_used += estimated_tokens

            # Fix #9: internal reranked_score is omitted from the XML to avoid
            # the LLM being influenced by or reasoning about internal scores.
            document = f"""
<doc
id="{idx}"
title="{metadata.get('title', '')}"
cluster="{metadata.get('cluster', '')}"
category="{metadata.get('category', '')}"
faculty_name="{metadata.get('faculty_name', '')}"
event_name="{metadata.get('event_name', '')}"
url="{metadata.get('url', '')}"
h1="{metadata.get('h1', '')}"
h2="{metadata.get('h2', '')}"
h3="{metadata.get('h3', '')}"
scraped_date="{metadata.get('scraped_date', '')}"
>
{chunk_text}

</doc>
"""
            documents.append(document)

            url = metadata.get("url")

            if url and url not in seen_urls:

                sources.append({
                    "title": metadata.get("title"),
                    "url": url,
                    "cluster": metadata.get("cluster")
                })

                seen_urls.add(url)

        context = (
            "<context>\n"
            + "\n".join(documents)
            + "\n</context>"
        )

        return {
            "context": context,
            "sources": sources
        }