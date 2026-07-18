import re

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
        # Rough token estimate: word count × 1.3 (accounts for sub-word splits).
        return int(len(text.split()) * 1.3)

    def build(self, chunks, retrieval_intent="general"):

        documents = []

        sources = []
        seen_urls = set()

        context_tokens_used = 0

        # Fix CB3: for policy_version queries, raise the token budget so that
        # version history sections — which often appear at the end of a long
        # policy document — are not dropped by the budget cap before they are
        # included in the context. 4000 tokens is still safe for all models
        # (system ~450 + history ~500 + 4000 = ~4950 tokens).
        effective_max_tokens = (
            4000 if retrieval_intent == "policy_version"
            else self.MAX_CONTEXT_TOKENS
        )

        for idx, chunk in enumerate(
            chunks,
            start=1
        ):

            metadata = chunk["metadata"]

            chunk_text = metadata.get("text", "")

            # Fix CB1: token estimate previously only included title/h1/h2 in
            # xml_attrs, underestimating the real XML overhead (12 attributes +
            # tag structure ≈ 250 chars). Estimate now covers the full document
            # string so the token budget is accurate and chunks aren't silently
            # over-admitted.
            xml_overhead_words = 50  # ~250 chars / avg 5 chars-per-word
            estimated_tokens = self._estimate_tokens(chunk_text) + xml_overhead_words

            # Fix G: enforce token budget — skip lower-ranked chunks that
            # would push us over the limit.
            if context_tokens_used + estimated_tokens > effective_max_tokens and idx > 1:
                break

            context_tokens_used += estimated_tokens

            # Fix CB2: added program_name attribute so the LLM knows which
            # program each chunk belongs to. Critical for comparison queries
            # ("compare BTech ICT vs BS-MS fees") where two chunks about
            # different programs would otherwise look identical to the model.
            # Fix #9: internal reranked_score is still omitted from the XML.
            # Fix CB4: rule_year extracted from title heuristically
            # (e.g. "Academic Requirements PhD wef 2024-25" → "2024-25")
            # and added as an XML attribute. This lets the LLM explicitly see
            # which year's document it is reading and cite the year correctly.
            # Fix CB5: moved `import re` to the top of the file (was imported
            # inside this loop on every chunk iteration, which is unnecessary).
            title_str = metadata.get("title", "")
            doc_rule_year = metadata.get("document_year", "")
            if not doc_rule_year:
                year_match = re.search(r"(20\d{2}[-\u2013]\d{2,4})", title_str)
                doc_rule_year = year_match.group(1) if year_match else ""

            start_line_val = metadata.get("start_line", "")
            end_line_val = metadata.get("end_line", "")

            document = f"""
<doc
id="{idx}"
title="{title_str}"
rule_year="{doc_rule_year}"
start_line="{start_line_val}"
end_line="{end_line_val}"
program_name="{metadata.get('program_name', '')}"
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
            relative_path = metadata.get("relative_path")

            # Fix CB6 (Phase C): previously a chunk was only ever cited if it
            # had a public "url" — internal-only markdown (no website URL)
            # silently produced no citation card at all. Dedup key now falls
            # back to relative_path, then title, so every retrieved chunk is
            # citeable. relative_path/start_line/end_line let the frontend
            # side-drawer open the exact source file and highlight the lines
            # this chunk was drawn from.
            dedup_key = url or relative_path or title_str

            if dedup_key and dedup_key not in seen_urls:

                sources.append({
                    "title": metadata.get("title"),
                    "url": url or None,
                    "path": relative_path or None,
                    "start_line": start_line_val or None,
                    "end_line": end_line_val or None,
                    "cluster": metadata.get("cluster")
                })

                seen_urls.add(dedup_key)

        context = (
            "<context>\n"
            + "\n".join(documents)
            + "\n</context>"
        )

        return {
            "context": context,
            "sources": sources
        }