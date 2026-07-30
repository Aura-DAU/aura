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
        seen_urls = {}
        # doc id (the `id` attribute the LLM cites) → index into `sources`.
        # Not the identity map: several chunks can dedup onto one source, and
        # a chunk whose source was already seen still gets its own doc id. So
        # sources[i] does NOT correspond to <doc id="i+1"> and callers must
        # resolve cited ids through this map rather than by position.
        citation_map = {}

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
            doc_rule_year = metadata.get("rule_year") or metadata.get("document_year", "")
            if doc_rule_year:
                doc_rule_year = str(doc_rule_year)
            if not doc_rule_year or not re.search(r"\d", doc_rule_year):
                search_targets = [
                    title_str,
                    metadata.get("h1", ""),
                    metadata.get("relative_path", "")
                ]
                for target in search_targets:
                    if not target:
                        continue
                    m4 = re.search(r"(?<!\d)(20\d{2})[\s\-_\u2013](\d{2}|\d{4})(?!\d)", target)
                    if m4:
                        y1_int = int(m4.group(1))
                        y2_int = int(m4.group(2)[-2:])
                        if y2_int == (y1_int + 1) % 100:
                            doc_rule_year = f"{y1_int}-{y2_int:02d}"
                            break
                    m2 = re.search(r"(?<!\d)(2\d)[\s\-_\u2013](\d{2})(?!\d)", target)
                    if m2:
                        y1 = int(m2.group(1))
                        y2 = int(m2.group(2))
                        if 20 <= y1 <= 35 and y2 == (y1 + 1) % 100:
                            doc_rule_year = f"20{y1:02d}-{y2:02d}"
                            break
                    # Bug fix: bare season/term + 2-digit year with no range
                    # given (e.g. "Winter25", "Autumn 2025") previously fell
                    # through this whole chain. Same convention as ingestion:
                    # Winter NN and Autumn NN both belong to academic year
                    # NN-(NN+1).
                    m3 = re.search(
                        r"(?i)\b(?:autumn|winter|monsoon|spring|summer)[\s_-]?(?:20)?(\d{2})\b(?![\s_-]?\d)",
                        target,
                    )
                    if m3:
                        y1 = int(m3.group(1))
                        if 20 <= y1 <= 35:
                            doc_rule_year = f"20{y1:02d}-{(y1 + 1) % 100:02d}"
                            break
                    m1 = re.search(r"(?<!\d)(20\d{2})(?!\d)", target)
                    if m1:
                        doc_rule_year = m1.group(1)
                        break
            if not doc_rule_year:
                doc_rule_year = ""

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

            if dedup_key:
                if dedup_key not in seen_urls:
                    seen_urls[dedup_key] = len(sources)

                    sources.append({
                        "title": metadata.get("title"),
                        "url": url or None,
                        "path": relative_path or None,
                        "start_line": start_line_val or None,
                        "end_line": end_line_val or None,
                        "cluster": metadata.get("cluster")
                    })
                else:
                    # Bug fix: a second chunk from the same document (dedup
                    # collapses it onto the existing source card) was
                    # previously invisible to the card's start_line/end_line —
                    # they stayed frozen on whichever chunk was seen first,
                    # even if THIS chunk is the one the model actually cites
                    # its answer from. Widen the line range to cover every
                    # chunk that maps to this source instead.
                    existing = sources[seen_urls[dedup_key]]
                    try:
                        if start_line_val and existing.get("start_line"):
                            existing["start_line"] = min(int(existing["start_line"]), int(start_line_val))
                        elif start_line_val and not existing.get("start_line"):
                            existing["start_line"] = start_line_val
                        if end_line_val and existing.get("end_line"):
                            existing["end_line"] = max(int(existing["end_line"]), int(end_line_val))
                        elif end_line_val and not existing.get("end_line"):
                            existing["end_line"] = end_line_val
                    except (TypeError, ValueError):
                        pass

                citation_map[idx] = seen_urls[dedup_key]

        context = (
            "<context>\n"
            + "\n".join(documents)
            + "\n</context>"
        )

        return {
            "context": context,
            "sources": sources,
            "citation_map": citation_map
        }