import logging
import os
from dotenv import load_dotenv
from pipeline.inference_router import InferenceRouter

logger = logging.getLogger(__name__)

_ASSISTANT_TURN_CHARS = 800
# Room for several questions; 120 tokens truncated multi-question rewrites.
_REWRITE_MAX_TOKENS = 300


class QueryRewriter:

    def __init__(self):
        load_dotenv()
        self.model = os.getenv(
            "VLLM_MODEL",
            "Qwen/Qwen3-32B-AWQ"
        )

    def rewrite(
        self,
        query,
        history=None,
        academic_scope=None,
    ):

        if not history:
            return query

        history_lines = []

        # Same 6-turn window as the answer generator. Long assistant answers
        # are cut: only their topic is needed to resolve a reference, and a
        # full (possibly wrong) answer invites the rewriter to copy facts.
        for turn in history[-6:]:
            content = str(turn.get("content") or "")
            if turn.get("role") == "assistant" and len(content) > _ASSISTANT_TURN_CHARS:
                content = content[:_ASSISTANT_TURN_CHARS] + " ..."
            history_lines.append(f"{turn.get('role', 'user')}: {content}")
        history_text = "\n".join(history_lines)

        scope_hint = ""
        if academic_scope is not None:
            scope_hint = (
                "Verified student context (use only to resolve references such as "
                "'my curriculum'; do not add it otherwise): "
                f"programme={academic_scope.programme_id}, "
                f"admission_year={academic_scope.admission_year}, "
                f"semester={academic_scope.current_semester}.\n\n"
            )

        prompt = f"""
You are the query rewriting component for AURA, the AI assistant for Dhirubhai Ambani University (DAU).

Rewrite the latest user question so it is fully self-contained.

Rules

- Resolve pronouns and references ("he", "it", "that program", "the second one",
  "what about M.Tech?") using only the conversation history.
- If the latest question starts a new topic, return it unchanged. Do not carry
  programmes, people or years from earlier turns into an unrelated question.
- Preserve the original intent exactly. Do not add, remove, or infer facts.
- Do not answer the question.

Output only the rewritten question, with no quotes, explanations or extra text.

{scope_hint}Conversation History:

{history_text}

Latest Question:

{query}
"""

        def _execute_rewrite(client):
            return client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=_REWRITE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                extra_body=InferenceRouter.no_think_extra_body(),
            )

        try:
            response = InferenceRouter.call_with_rotation(_execute_rewrite, max_retries=3)
            rewritten = (response.choices[0].message.content or "").strip().strip('"')
        except Exception as exc:
            # A rewriter outage must not fail the request; the original
            # question still retrieves reasonably for most follow-ups.
            logger.warning("query rewrite failed; using original question: %s", exc)
            return query

        # Keep every line: a follow-up holding several questions is rewritten
        # as several lines, and taking only the first silently dropped the rest.
        rewritten = " ".join(
            line.strip() for line in rewritten.splitlines() if line.strip()
        )[:1200]
        return rewritten or query
