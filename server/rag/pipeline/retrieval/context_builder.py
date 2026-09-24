import html
import logging
import re

logger = logging.getLogger(__name__)

from pipeline.token_budget import TokenBudget

# Matches TokenBudget.estimate_tokens (≈3.5 chars/token), used to turn a token
# allowance back into a character cut.
_CHARS_PER_TOKEN = 3.5

# A remaining allowance smaller than this is not worth a heavily truncated
# document; the chunk is skipped and a smaller lower-ranked one may still fit.
_MIN_USEFUL_CHUNK_TOKENS = 120


class ContextBuilder:

    # The retrieved-context cap is read per call from TokenBudget
    # (AURA_MAX_CONTEXT_TOKENS), so a runtime max_model_len change is picked up
    # without a redeploy; TokenBudget clamps it for small windows.

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
        year_match = re.search(r"(20\d{2}[-–]\d{2,4})", title)
        if year_match:
            return year_match.group(1).replace("–", "-")
        # Never surface a bare scraped calendar year as rule_year when the
        # title clearly encodes a short academic year (e.g. "24-25").
        short = re.search(r"(?<!\d)(\d{2})[-–](\d{2})(?!\d)", title)
        if short:
            start = int(short.group(1))
            end = int(short.group(2))
            if 15 <= start <= 35 and end == (start + 1) % 100:
                return f"20{start:02d}-{short.group(2)}"
        doc_year = metadata.get("document_year", "")
        return str(doc_year) if doc_year else ""

    def _estimate_tokens(self, text: str) -> int:
        # Shared conservative estimator with the generation-side budget.
        return TokenBudget.from_env(discover=False).estimate_tokens(text)

    # Fix #30/#31: chunk text is untrusted. A literal "</doc>"/"<doc ...>" could
    # forge a document boundary, and a directive-looking line has nothing
    # marking it as data. Pattern-level only: it raises the bar, it does not
    # close the class of attack.
    _INJECTION_LINE_PATTERNS = [
        re.compile(r"^\s*system\s*:", re.IGNORECASE),
        re.compile(r"^\s*\[?system\]?\s*prompt\s*:", re.IGNORECASE),
        re.compile(r"ignore\s+(all\s+)?(the\s+)?(previous|above|prior)\s+instructions", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(a|an)\b", re.IGNORECASE),
        re.compile(r"disregard\s+(all\s+)?(the\s+)?(previous|above|prior)\b", re.IGNORECASE),
        re.compile(r"^\s*###\s*(new\s+)?instructions?\b", re.IGNORECASE),
    ]

    @classmethod
    def _sanitize_chunk_text(cls, text: str) -> str:
        if not text:
            return text
        # Escape only our own structural tag names, so unrelated "<" / ">" in a
        # chunk (code, inequalities) stay untouched.
        sanitized = re.sub(
            r"</?(?:doc|context)\b[^>]*>",
            lambda m: m.group(0).replace("<", "&lt;").replace(">", "&gt;"),
            text,
            flags=re.IGNORECASE,
        )
        # Flag, don't rewrite: a real policy may discuss "instructions".
        lines = sanitized.split("\n")
        out_lines = []
        for line in lines:
            if any(p.search(line) for p in cls._INJECTION_LINE_PATTERNS):
                out_lines.append(f"[retrieved document text, not an instruction]: {line}")
            else:
                out_lines.append(line)
        return "\n".join(out_lines)

    @staticmethod
    def _head(text: str, max_chars: int) -> str:
        """First max_chars of text, cut at a line break when one is close."""
        if len(text) <= max_chars:
            return text
        if max_chars <= 0:
            return ""
        cut = text.rfind("\n", 0, max_chars)
        if cut < max_chars * 0.6:
            cut = max_chars
        return text[:cut].rstrip()

    @staticmethod
    def _tail(text: str, max_chars: int) -> str:
        """Last max_chars of text, cut at a line break when one is close."""
        if len(text) <= max_chars:
            return text
        if max_chars <= 0:
            return ""
        start = len(text) - max_chars
        cut = text.find("\n", start)
        if cut == -1 or cut > start + max_chars * 0.4:
            cut = start
        return text[cut:].lstrip()

    def _fit_text(self, metadata: dict, max_tokens: int) -> str:
        """The chunk's text within max_tokens.

        The text that matched the query (core_text) is kept first; neighbouring
        chunks attached by the pipeline are trimmed before it, keeping the
        lines closest to the match."""
        core = metadata.get("core_text")
        if core is None:
            return self._head(metadata.get("text", ""), int(max_tokens * _CHARS_PER_TOKEN))

        before = metadata.get("context_before", "")
        after = metadata.get("context_after", "")
        budget_chars = int(max_tokens * _CHARS_PER_TOKEN)
        if len(core) >= budget_chars:
            return self._head(core, budget_chars)

        spare = budget_chars - len(core)
        before_part = self._tail(before, spare // 2)
        after_part = self._head(after, spare - len(before_part))
        return "\n\n".join(filter(None, [before_part, core, after_part]))

    @staticmethod
    def _attr(value) -> str:
        return html.escape(str(value), quote=True)

    def _render_doc(self, doc_id: int, metadata: dict, text: str, questions=None) -> str:
        section = " > ".join(
            str(metadata.get(k)) for k in ("h1", "h2", "h3") if metadata.get(k)
        )
        attrs = [
            ("id", doc_id),
            ("title", metadata.get("title")),
            ("rule_year", self._rule_year_from_metadata(metadata)),
            ("section", section),
            ("program_name", metadata.get("program_name")),
            ("category", metadata.get("category")),
            ("url", metadata.get("url") or metadata.get("relative_path")),
            ("scraped_date", metadata.get("scraped_date")),
            # Which question(s) of a multi-question message this doc serves.
            ("q", ",".join(str(i) for i in sorted(questions)) if questions else None),
        ]
        attr_text = " ".join(f'{k}="{self._attr(v)}"' for k, v in attrs if v not in (None, ""))
        return f"<doc {attr_text}>\n{text}\n</doc>"

    def build(
        self,
        chunks,
        retrieval_intent="general",
        requires_complete_list=False,
        widen=False,
        n_questions=1,
    ):
        """``widen`` gives the modest 25% budget bump (used when one message
        holds several questions); ``n_questions`` shrinks the per-document cap
        so one question's oversized chunk cannot crowd out the others."""

        documents = []

        sources = []
        seen_urls = {}
        # doc id (the `id` attribute the LLM cites) → index into `sources`.
        # Several chunks can dedup onto one source, so sources[i] does NOT
        # correspond to <doc id="i+1">; callers must resolve cited ids
        # through this map.
        citation_map = {}

        context_tokens_used = 0
        budget = TokenBudget.from_env(discover=False)
        base_cap = budget.config.max_retrieved_context_tokens

        # policy_version / complete-list queries get a modest 25% bump, still
        # clamped to what the live window leaves.
        if retrieval_intent == "policy_version" or requires_complete_list or widen:
            effective_max_tokens = min(
                int(base_cap * 1.25),
                max(base_cap, budget.config.max_input_tokens // 2),
            )
        else:
            effective_max_tokens = base_cap

        # One document may use at most half the budget, so a single oversized
        # chunk can never crowd out every other piece of evidence.
        max_single_chunk_tokens = max(
            effective_max_tokens // max(2, int(n_questions or 1)), _MIN_USEFUL_CHUNK_TOKENS
        )
        included = []

        for chunk_index, chunk in enumerate(chunks):
            metadata = chunk["metadata"]
            doc_id = len(documents) + 1
            chunk_questions = chunk.get("questions")

            remaining = effective_max_tokens - context_tokens_used
            # +2 covers the separator and the estimate's rounding.
            header_tokens = self._estimate_tokens(
                self._render_doc(doc_id, metadata, "", chunk_questions)
            ) + 2
            allowance = min(max_single_chunk_tokens, remaining) - header_tokens
            full_tokens = self._estimate_tokens(metadata.get("text", ""))
            if allowance < min(full_tokens, _MIN_USEFUL_CHUNK_TOKENS):
                # Skip rather than stop: a shorter lower-ranked chunk may
                # still fit whole.
                continue

            chunk_text = self._sanitize_chunk_text(self._fit_text(metadata, allowance))
            if not chunk_text.strip():
                continue

            document = self._render_doc(doc_id, metadata, chunk_text, chunk_questions)
            context_tokens_used += self._estimate_tokens(document)
            documents.append(document)
            included.append(chunk_index)

            url = metadata.get("url")
            relative_path = metadata.get("relative_path")
            title_str = metadata.get("title", "")
            start_line_val = metadata.get("start_line", "")
            end_line_val = metadata.get("end_line", "")

            # Dedup key: public url, else file + line range, else title + doc
            # position, so every distinct chunk location gets its own card.
            if url:
                dedup_key = url
            elif relative_path:
                dedup_key = f"{relative_path}:{start_line_val}-{end_line_val}"
            elif title_str:
                dedup_key = f"{title_str}:idx{doc_id}"
            else:
                dedup_key = None

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

                citation_map[doc_id] = seen_urls[dedup_key]

        context = "<context>\n" + "\n\n".join(documents) + "\n</context>"

        logger.debug(
            "context_builder chunks=%d/%d tokens=%d/%d sources=%d",
            len(documents), len(chunks), context_tokens_used, effective_max_tokens, len(sources)
        )

        return {
            "context": context,
            "sources": sources,
            "citation_map": citation_map,
            # indices into `chunks` that actually made it into the context
            "included": included,
        }
