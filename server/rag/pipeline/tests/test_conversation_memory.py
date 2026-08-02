"""ConversationMemory budgeting — including the turn-count compaction trigger
that keeps the unsummarised tail under the API's 20-turn history cap."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.exceptions import ContextLengthExceeded
from pipeline.memory.conversation_memory import (
    ConversationMemory,
    _approx_tokens,
)


def _turns(n: int, content: str = "short") -> list[dict]:
    # Alternate roles so it looks like a real transcript; content is tiny so
    # the token budget alone would never force compaction.
    out = []
    for i in range(n):
        out.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"{content} {i}"})
    return out


def test_prepare_compacts_when_tail_exceeds_max_tail_turns():
    folded: list[list] = []

    def fake_summariser(prior, older):
        folded.append(list(older))
        return (prior + "\n" if prior else "") + f"folded:{len(older)}"

    mem = ConversationMemory(summariser=fake_summariser)
    mem.max_tail_turns = 6
    mem.keep_verbatim = 4
    mem.min_verbatim = 2

    history = _turns(10)
    result = mem.prepare("", history)

    assert result.summary_changed is True
    assert result.folded_turns == 6  # 10 - keep_verbatim(4)
    assert len(result.history) == 4
    assert folded and len(folded[0]) == 6


def test_prepare_skips_llm_when_tail_fits_under_max_tail_turns():
    calls = {"n": 0}

    def fake_summariser(prior, older):
        calls["n"] += 1
        return "should not run"

    mem = ConversationMemory(summariser=fake_summariser)
    mem.max_tail_turns = 16

    result = mem.prepare("", _turns(10))
    assert result.summary_changed is False
    assert result.folded_turns == 0
    assert len(result.history) == 10
    assert calls["n"] == 0


def test_max_tail_turns_default_stays_under_api_history_cap():
    # schemas.ChatRequest and the Next.js Zod schema both cap history at 20.
    # The default trigger must sit below that so a compacting request still fits.
    mem = ConversationMemory(summariser=lambda p, o: p or "x")
    assert mem.max_tail_turns <= 20
    assert mem.max_tail_turns >= mem.keep_verbatim


def test_default_budget_leaves_room_at_a_4096_window():
    # Regression: the pre-4096 defaults made this negative, so _raw_budget
    # clamped to 0 and every conversation compacted into an empty budget.
    mem = ConversationMemory(summariser=lambda p, o: "x")
    assert mem._raw_budget > 0
    assert mem.history_budget > mem.summary_max_tokens


def test_summariser_context_length_error_does_not_reach_the_caller():
    """A context-length 400 from the digest call must degrade, never 500.

    _ask_with_memory runs this before generation and there is no FastAPI
    handler for RAGPipelineError, so anything escaping here becomes a 500.
    """
    mem = ConversationMemory()
    mem.model_context_tokens = 400
    mem.reserved_answer = mem.reserved_context = mem.reserved_system = 0
    mem.safety_margin = 0
    mem._forced_summary_max = 20
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 400}
        for i in range(8)
    ]

    with patch(
        "pipeline.inference_router.InferenceRouter.call_with_rotation",
        side_effect=ContextLengthExceeded(),
    ):
        result = mem.prepare("PRIOR", history)

    # Fell back to the extractive digest instead of propagating.
    assert result.summary.startswith("PRIOR")
    assert result.folded_turns > 0
    assert len(result.history) >= mem.min_verbatim


def test_summariser_prompt_is_clamped_to_the_context_window():
    """The digest request itself must fit, or it is a guaranteed 400.

    `older` is unbounded, so without a clamp a long fold sends a prompt larger
    than the window and the LLM digest silently stops working.
    """
    sent: list[str] = []

    class _Choice:
        message = type("M", (), {"content": "digest"})()

    class _Resp:
        choices = [_Choice()]

    def _capture(call, max_retries=3):
        class _Client:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        sent.extend(m["content"] for m in kwargs["messages"])
                        return _Resp()

        return call(_Client())

    mem = ConversationMemory()
    mem.model_context_tokens = 2048
    mem._forced_summary_max = 200
    # ~50k tokens of transcript — 25× the window if sent unclamped.
    older = [{"role": "user", "content": "q" * 100_000}]

    with patch(
        "pipeline.inference_router.InferenceRouter.call_with_rotation",
        side_effect=_capture,
    ), patch("pipeline.inference_router.InferenceRouter.model_name", return_value="m"), patch(
        "pipeline.inference_router.InferenceRouter.no_think_extra_body", return_value={}
    ):
        assert mem._default_summariser("PRIOR", older) == "digest"

    prompt_tokens = sum(_approx_tokens(part) for part in sent)
    assert prompt_tokens + mem.summary_max_tokens <= mem.model_context_tokens
