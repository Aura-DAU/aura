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
    # Import centralized token budget configuration
    try:
        from config.token_budget_config import LLM_MAX_CONTEXT_BUDGET
        MAX_CONTEXT_TOKENS = LLM_MAX_CONTEXT_BUDGET
    except ImportError:
        MAX_CONTEXT_TOKENS = 4000

    @staticmethod
    def _rule_year_from_metadata(metadata: dict) -> str:
        """Prefer title/path academic labels over ingest scraped_date years.

        Club Committee Data 24-25 was being labeled rule_year=2026 because
        document_year was taken from scraped_date. Title/filename win here
        even for already-indexed chunks that still carry the bad year.
        """
        # Local import keeps this file free of package-path coupling for tests
        # that import ContextBuilder without the full ingestion package.
        try:
            from pipeline.ingestion.chunking.metadata_extractors import (
                normalize_academic_year_label,
            )
        except ImportError:
            normalize_academic_year_label = None  # type: ignore[assignment]

        title = str(metadata.get("title") or "")
        source_file = str(metadata.get("source_file") or metadata.get("relative_path") or "")
        academic = metadata.get("academic_year")
        candidates = [academic, title, source_file]
        if normalize_academic_year_label:
            for raw in candidates:
                label = normalize_academic_year_label(raw)
                if label:
                    return label
        # Fallback: full 20xx-yy in title only (legacy behaviour).
        year_match = re.search(r"(20\d{2}[-\u2013]\d{2,4})", title)
        if year_match:
            return year_match.group(1).replace("\u2013", "-")
        # Never surface a bare scraped calendar year as rule_year when the
        # title clearly encodes a short academic year (e.g. "24-25").
        short = re.search(r"(?<!\d)(\d{2})[-\u2013](\d{2})(?!\d)", title)
        if short:
            start = int(short.group(1))
            end = int(short.group(2))
            if 15 <= start <= 35 and end == (start + 1) % 100:
                return f"20{start:02d}-{short.group(2)}"
        doc_year = metadata.get("document_year", "")
        return str(doc_year) if doc_year else ""

    def _estimate_tokens(self, text: str) -> int:
        # Rough token estimate: word count × 1.3 (accounts for sub-word splits).
        return int(len(text.split()) * 1.3)

    def build(self, chunks, retrieval_intent="general", requires_complete_list=False):

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
        #
        # Fix CB7 / TK2: requires_complete_list queries (enumerations like
        # "which clubs does DAU have", negation questions) get the same
        # widened budget — raising final_top_k in retrieval_pipeline.py to 15
        # for these queries had no effect while this budget stayed at 3000,
        # since the extra chunks would just get dropped again by the
        # token-budget `break` below.
        effective_max_tokens = (
            4000 if retrieval_intent == "policy_version" or requires_complete_list
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
            # Fix CB4 / CB4b: rule_year from title/filename academic label —
            # never prefer scraped_date-derived document_year when the title
            # encodes a real roster year (24-25, 2025-26, 2026-27).
            title_str = metadata.get("title", "")
            doc_rule_year = self._rule_year_from_metadata(metadata)

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