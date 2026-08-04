"""Unit tests for ConversationMemory.

These use an injected fake summariser, so they exercise the full budgeting /
compaction / fork logic with no network or LLM dependency (importable under the
local py3.14 env that lacks the vLLM/pinecone stack).
"""

from pipeline.memory.conversation_memory import (
    ConversationMemory,
    MemoryResult,
    _approx_tokens,
)


def _turn(role: str, chars: int) -> dict:
    return {"role": role, "content": "x" * chars}


def _mem(**overrides) -> ConversationMemory:
    """A memory instance with a fake summariser and small, deterministic budgets.

    The fake records what it was asked to fold and returns a fixed-size summary
    so `should_fork` (over summary cap) is controllable per test.
    """
    calls = []

    def fake_summariser(prior, older):
        calls.append((prior, list(older)))
        return "SUMMARY(" + str(len(older)) + " turns)"

    mem = ConversationMemory(summariser=fake_summariser)
    mem.calls = calls  # type: ignore[attr-defined]
    # Force a small, predictable budget: raw budget = model_context only.
    mem.reserved_answer = 0
    mem.reserved_context = 0
    mem.reserved_system = 0
    mem.safety_margin = 0
    mem.model_context_tokens = 400  # tokens
    mem._forced_summary_max = 20
    mem.keep_verbatim = 4
    for k, v in overrides.items():
        setattr(mem, k, v)
    return mem


def test_fast_path_leaves_short_history_untouched():
    mem = _mem()
    history = [_turn("user", 40), _turn("assistant", 40)]  # ~20 tokens total
    result = mem.prepare("", history)

    assert isinstance(result, MemoryResult)
    assert result.folded_turns == 0
    assert result.summary_changed is False
    assert result.should_fork is False
    assert result.history == history
    assert mem.calls == []  # no summariser call on the fast path


def test_over_budget_folds_oldest_turns_into_summary():
    mem = _mem()
    # 8 turns × ~100 tokens each = ~800 tokens >> 400-token budget.
    history = [_turn("user" if i % 2 == 0 else "assistant", 400) for i in range(8)]
    result = mem.prepare("", history)

    assert result.summary_changed is True
    assert result.folded_turns > 0
    # Verbatim tail is capped at keep_verbatim and preserves the most recent turns.
    assert len(result.history) <= mem.keep_verbatim
    assert result.history == history[-len(result.history):]
    # folded + kept == everything we were given (nothing is silently dropped).
    assert result.folded_turns + len(result.history) == len(history)
    assert len(mem.calls) == 1
    # The summariser receives exactly the folded (oldest) turns.
    _prior, folded = mem.calls[0]
    assert folded == history[: result.folded_turns]


def test_existing_summary_is_passed_to_summariser_for_merge():
    mem = _mem()
    history = [_turn("user" if i % 2 == 0 else "assistant", 400) for i in range(8)]
    mem.prepare("PRIOR MEMORY", history)

    prior, _folded = mem.calls[0]
    assert prior == "PRIOR MEMORY"


def test_always_keeps_last_exchange_verbatim():
    mem = _mem(min_verbatim=2, keep_verbatim=2)
    history = [_turn("user" if i % 2 == 0 else "assistant", 600) for i in range(6)]
    result = mem.prepare("", history)

    # Even though every turn is huge, the last two survive verbatim.
    assert len(result.history) == 2
    assert result.history == history[-2:]


def test_should_fork_when_summary_exceeds_its_cap():
    # Summariser returns a summary far bigger than summary_max_tokens → hard
    # overflow → one fork with a bounded continuation seed.
    def big_summariser(prior, older):
        return "y" * 5000  # ~1250 tokens, well over the 20-token cap

    mem = _mem()
    mem._summarise = big_summariser  # type: ignore[assignment]
    history = [_turn("user" if i % 2 == 0 else "assistant", 400) for i in range(8)]
    result = mem.prepare("", history)

    assert result.should_fork is True
    assert _approx_tokens(result.summary) <= mem.summary_max_tokens

    continuation = mem.prepare(result.summary, [])
    assert continuation.should_fork is False


def test_oversized_incoming_continuation_seed_self_heals_once():
    mem = _mem()

    result = mem.prepare("z" * 5000, [])

    assert result.should_fork is True
    assert result.summary_changed is True
    assert _approx_tokens(result.summary) <= mem.summary_max_tokens
    assert mem.prepare(result.summary, []).should_fork is False


def test_summariser_failure_falls_back_without_raising():
    def boom(prior, older):
        raise RuntimeError("vLLM down")

    mem = _mem()
    mem._summarise = boom  # type: ignore[assignment]
    history = [
        {"role": "user", "content": "q" * 400},
        {"role": "assistant", "content": "a" * 400},
        {"role": "user", "content": "latest" + "q" * 400},
        {"role": "assistant", "content": "a" * 400},
        {"role": "user", "content": "z" * 400},
        {"role": "assistant", "content": "a" * 400},
    ]
    result = mem.prepare("PRIOR", history)

    # Did not raise; kept prior memory and preserved a recent verbatim tail.
    assert result.summary.startswith("PRIOR")
    assert len(result.history) >= mem.min_verbatim
    assert result.folded_turns > 0


def test_blank_and_none_inputs_are_safe():
    mem = _mem()
    assert mem.prepare(None, None) == MemoryResult("", [], 0, False, False)
    # Turns with empty content are dropped.
    result = mem.prepare("  ", [{"role": "user", "content": ""}])
    assert result.history == []


def test_pointer_math_across_two_compactions():
    """folded_turns from successive calls sum to the number archived, mirroring
    how the client advances summaryTurnCount."""
    mem = _mem()
    history = [_turn("user" if i % 2 == 0 else "assistant", 400) for i in range(8)]

    first = mem.prepare("", history)
    pointer = first.folded_turns
    # Client would next send summary + messages[pointer:]; simulate more turns.
    tail = history[pointer:] + [_turn("user", 400), _turn("assistant", 400)]
    second = mem.prepare(first.summary, tail)

    assert second.folded_turns >= 0
    # Nothing lost: everything in the second tail is either folded or kept.
    assert second.folded_turns + len(second.history) == len(tail)
