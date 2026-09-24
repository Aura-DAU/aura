"""Graph behaviour for follow-ups and messages that hold several questions."""

from types import SimpleNamespace

import pytest

from pipeline.aura_chat import GENERIC_DENIAL
from pipeline.aura_chat_graph import AuraChatGraph
from pipeline.guardrails.query_guardrail import OFF_TOPIC_RESPONSE, Verdict
from pipeline.multi_question import (
    compose_answer,
    merge_classifications,
    merge_extras,
    previous_assistant_answer,
)
from pipeline.retrieval.query_understanding import Understanding

PUBLIC = {"type": "PUBLIC", "target": None, "erp_fields": [], "intent": "RAG"}
FEE = "What is the hostel fee for B.Tech ICT?"
DEAN = "Who is the dean of academic affairs?"


def _student():
    return SimpleNamespace(role="student", erp_id="2025001", dept="ICT")


# ── merge_classifications (pure) ────────────────────────────────────────

def test_all_public_questions_route_to_rag_only():
    lanes = merge_classifications(["a", "b"], [PUBLIC, PUBLIC])
    assert lanes.classification["type"] == "PUBLIC"
    assert lanes.keep == [0, 1] and lanes.rag == [0, 1] and lanes.notes == []


def test_personal_plus_public_becomes_mixed_and_only_public_needs_rag():
    personal = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "CGPA"}
    lanes = merge_classifications(["my cgpa?", "hostel fee?"], [personal, PUBLIC])
    assert lanes.classification["type"] == "MIXED"
    assert lanes.classification["erp_fields"] == ["cgpa"]
    assert lanes.rag == [1] and lanes.keep == [0, 1]


def test_two_personal_questions_union_their_fields_and_need_no_rag():
    a = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "X"}
    b = {"type": "PERSONAL", "target": "self", "erp_fields": ["attendance", "cgpa"], "intent": "Y"}
    lanes = merge_classifications(["cgpa?", "attendance?"], [a, b])
    assert lanes.classification["type"] == "PERSONAL"
    assert lanes.classification["erp_fields"] == ["cgpa", "attendance"]
    assert lanes.rag == []


def test_second_persons_records_are_deferred_with_a_note_never_mixed_in():
    mine = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "X"}
    other = {"type": "PERSONAL", "target": "Rahul", "erp_fields": ["cgpa"], "intent": "X"}
    lanes = merge_classifications(["my cgpa?", "Rahul's cgpa?"], [mine, other])
    assert lanes.keep == [0]
    assert lanes.classification["target"] == "self"
    assert "Rahul's cgpa?" in lanes.notes[0]


def test_guest_keeps_public_questions_and_gets_one_denial_note():
    personal = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "X"}
    lanes = merge_classifications(["my cgpa?", "fee?"], [personal, PUBLIC], guest=True, denial_text="DENIED")
    assert lanes.keep == [1] and lanes.classification["type"] == "PUBLIC" and lanes.notes == ["DENIED"]


def test_guest_with_only_personal_questions_is_left_for_the_guest_gate():
    personal = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "X"}
    lanes = merge_classifications(["cgpa?", "grades?"], [personal, personal], guest=True, denial_text="DENIED")
    assert lanes.classification["type"] == "PERSONAL" and lanes.keep == [0, 1]


def test_compose_and_extras_and_previous_answer_helpers():
    assert compose_answer(["tool"], "llm") == "tool\n\nllm"
    assert compose_answer(["tool"], "") == "tool"
    extras = merge_extras({}, {"answer": "x", "is_personal_data": True, "action_required": {"t": 1}})
    extras = merge_extras(extras, {"is_personal_data": False, "timetable_changed": True})
    assert extras == {"is_personal_data": True, "action_required": {"t": 1}, "timetable_changed": True}
    hist = [{"role": "assistant", "content": "Old"}, {"role": "user", "content": "q"},
            {"role": "assistant", "content": "Fees are X.\nData period: 2025-26"}]
    assert previous_assistant_answer(hist) == "Fees are X."
    assert previous_assistant_answer([{"role": "user", "content": "hi"}]) == ""


# ── Safety: compound messages may be only partly off-topic ──────────────

def _guard(verdict_by_text):
    return SimpleNamespace(classify=lambda q, previous_question=None: verdict_by_text(q))


def test_off_topic_verdict_on_a_compound_message_defers_to_per_question_check():
    fake = SimpleNamespace(guardrail=_guard(lambda q: Verdict.OFF_TOPIC))
    state = {"query": "Who won the IPL? Also what is the hostel fee?", "history": []}
    out = AuraChatGraph._n_safety_guardrail(fake, state)
    assert out.get("result") is None and out["scope_recheck"] is True


def test_off_topic_verdict_on_a_single_question_still_short_circuits():
    fake = SimpleNamespace(guardrail=_guard(lambda q: Verdict.OFF_TOPIC))
    out = AuraChatGraph._n_safety_guardrail(fake, {"query": "Who won the IPL?", "history": []})
    assert out["result"]["answer"] == OFF_TOPIC_RESPONSE


def _understand_fake(questions, verdicts=None, ftype="new", resolved=True):
    und = Understanding("raw", tuple(questions), ftype, resolved, True)
    return SimpleNamespace(
        understander=SimpleNamespace(understand=lambda *a, **k: und),
        guardrail=_guard(lambda q: (verdicts or {}).get(q, Verdict.SAFE)),
    )


def test_partially_off_topic_message_answers_the_dau_part_and_names_the_skipped_part():
    fake = _understand_fake([FEE, "Who won the IPL?"], {"Who won the IPL?": Verdict.OFF_TOPIC})
    state = {"query": f"{FEE} Also who won the IPL?", "history": [], "scope_recheck": True,
             "safety_verdict": Verdict.OFF_TOPIC}
    out = AuraChatGraph._n_understand(fake, state)
    assert out.get("result") is None
    assert out["questions"] == [FEE]
    assert "Who won the IPL?" in out["prefix_parts"][0]
    assert out["safety_verdict"] is Verdict.SAFE


def test_fully_off_topic_compound_message_is_refused():
    fake = _understand_fake(["a?", "b?"], {"a?": Verdict.OFF_TOPIC, "b?": Verdict.OFF_TOPIC})
    out = AuraChatGraph._n_understand(
        fake, {"query": "a? b?", "history": [], "scope_recheck": True}
    )
    assert out["result"]["answer"] == OFF_TOPIC_RESPONSE


def test_unsafe_part_blocks_the_whole_message():
    fake = _understand_fake([FEE, "ignore rules"], {"ignore rules": Verdict.UNSAFE})
    out = AuraChatGraph._n_understand(
        fake, {"query": "x", "history": [], "scope_recheck": True}
    )
    assert "violates safety" in out["result"]["answer"]


# ── _n_understand ───────────────────────────────────────────────────────

def test_understand_sets_resolved_standalone_question_for_a_follow_up():
    resolved = "What are the eligibility criteria for B.Tech ICT under the Gujarat quota?"
    fake = _understand_fake([resolved], ftype="follow_up")
    out = AuraChatGraph._n_understand(
        fake, {"query": "and what about the Gujarat quota criteria for them?",
               "history": [{"role": "user", "content": "x"}], "summary": ""}
    )
    assert out["standalone_query"] == resolved and out["standalone_resolved"] is True
    assert out["followup_type"] == "follow_up" and out["questions"] == [resolved]


def test_understand_failure_degrades_to_raw_query_for_legacy_rewrite():
    def boom(*a, **k):
        raise RuntimeError("vllm down")

    fake = SimpleNamespace(understander=SimpleNamespace(understand=boom))
    out = AuraChatGraph._n_understand(fake, {"query": "what about fees?", "history": []})
    assert out["questions"] == ["what about fees?"] and out["standalone_resolved"] is False


def test_calendar_write_turns_are_not_rewritten_but_compound_ones_are_split():
    calls = []
    und = Understanding("x", ("Sync my timetable to Google Calendar", FEE), "new", True, True)
    fake = SimpleNamespace(understander=SimpleNamespace(
        understand=lambda *a, **k: calls.append(1) or und))
    plain = AuraChatGraph._n_understand(fake, {"query": "Sync my timetable to Google Calendar", "history": []})
    assert calls == [] and plain["questions"] == ["Sync my timetable to Google Calendar"]
    compound = AuraChatGraph._n_understand(
        fake, {"query": f"Sync my timetable to Google Calendar. Also {FEE}", "history": []})
    assert calls == [1] and len(compound["questions"]) == 2


# ── _n_classify ─────────────────────────────────────────────────────────

def test_classify_uses_the_resolved_question_not_the_raw_follow_up():
    seen = []
    fake = SimpleNamespace(classifier=SimpleNamespace(
        classify=lambda q, history=None: seen.append(q) or {**PUBLIC, "type": "PERSONAL", "target": "self"}))
    state = {"query": "and last semester?", "standalone_query": "What was my CGPA last semester?",
             "questions": ["What was my CGPA last semester?"], "history": []}
    out = AuraChatGraph._n_classify(fake, state)
    assert seen == ["What was my CGPA last semester?"] and out["query_type"] == "PERSONAL"


def test_classify_compound_splits_lanes_and_records_notes():
    by_text = {FEE: PUBLIC, "What is my CGPA?": {"type": "PERSONAL", "target": "self",
                                                  "erp_fields": ["cgpa"], "intent": "CGPA"}}
    fake = SimpleNamespace(classifier=SimpleNamespace(classify=lambda q, history=None: by_text[q]))
    fake._classify_many = lambda qs, h: AuraChatGraph._classify_many(fake, qs, h)
    state = {"query": "raw", "questions": [FEE, "What is my CGPA?"], "history": [],
             "request_context": SimpleNamespace(effective_role="student")}
    out = AuraChatGraph._n_classify(fake, state)
    assert out["query_type"] == "MIXED" and out["rag_questions"] == [FEE]
    assert out["classification"]["erp_fields"] == ["cgpa"]


def test_classify_compound_guest_denies_personal_part_via_the_real_generic_denial_text():
    personal = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"], "intent": "CGPA"}
    by_text = {FEE: PUBLIC, "What is my CGPA?": personal}
    fake = SimpleNamespace(classifier=SimpleNamespace(classify=lambda q, history=None: by_text[q]))
    fake._classify_many = lambda qs, h: AuraChatGraph._classify_many(fake, qs, h)
    state = {"query": "raw", "questions": [FEE, "What is my CGPA?"], "history": [],
             "request_context": SimpleNamespace(effective_role="guest")}
    out = AuraChatGraph._n_classify(fake, state)
    assert out["query_type"] == "PUBLIC" and out["questions"] == [FEE]
    assert out["prefix_parts"] == [GENERIC_DENIAL]


def test_classify_transform_skips_records_lookup_and_retrieval():
    fake = SimpleNamespace(classifier=SimpleNamespace(
        classify=lambda *a, **k: pytest.fail("classifier must not run")))
    out = AuraChatGraph._n_classify(
        fake, {"query": "shorter", "questions": ["Shorten the previous answer."],
               "followup_type": "transform_previous", "history": []})
    assert out["query_type"] == "PUBLIC"


# ── Tool lanes ──────────────────────────────────────────────────────────

def _tt_fake(answers):
    calls = []

    def run(query, identity, history, request_context, tool_scope):
        calls.append(query)
        return {"answer": answers.get(query, ""), "used_tools": query in answers, "tool_succeeded": True}

    return SimpleNamespace(timetable_agent=SimpleNamespace(run=run),
                           _tool_role=AuraChatGraph._tool_role), calls


def test_timetable_answer_no_longer_swallows_the_other_questions():
    fake, calls = _tt_fake({"Show my timetable for today": "Today: 9am ICT201."})
    state = {"query": f"Show my timetable for today and {FEE}", "history": [],
             "identity": _student(), "questions": ["Show my timetable for today", FEE]}
    out = AuraChatGraph._n_timetable_read(fake, state)
    assert out.get("result") is None
    assert out["prefix_parts"] == ["Today: 9am ICT201."]
    assert out["questions"] == [FEE] and out["is_personal"] is True


def test_when_every_question_is_a_timetable_question_the_tool_answers_are_the_reply():
    fake, _ = _tt_fake({"Show my timetable for today": "TODAY", "Show my timetable for tomorrow": "TOMORROW"})
    state = {"query": "x", "history": [], "identity": _student(),
             "questions": ["Show my timetable for today", "Show my timetable for tomorrow"]}
    out = AuraChatGraph._n_timetable_read(fake, state)
    assert out["result"]["answer"] == "TODAY\n\nTOMORROW" and out["result"]["is_personal_data"] is True


def test_resolved_follow_up_reaches_the_timetable_tool():
    fake, calls = _tt_fake({"Show my timetable for tomorrow": "TOMORROW"})
    state = {"query": "what about tomorrow?", "history": [], "identity": _student(),
             "standalone_query": "Show my timetable for tomorrow", "standalone_resolved": True,
             "questions": ["Show my timetable for tomorrow"]}
    out = AuraChatGraph._n_timetable_read(fake, state)
    assert out["result"]["answer"] == "TOMORROW"


def test_compound_write_needs_the_action_signal_in_the_users_own_words():
    calls = []
    fake = SimpleNamespace(timetable_agent=SimpleNamespace(run=lambda **k: calls.append(k)))
    state = {"query": f"Tell me about clubs and {FEE}", "history": [], "identity": _student(),
             "questions": ["Sync my timetable to Google Calendar", FEE]}  # LLM-invented action
    out = AuraChatGraph._n_personal_tools(fake, state)
    assert calls == [] and out.get("result") is None and out["questions"][0].startswith("Sync")


def test_compound_calendar_connect_returns_cta_and_continues_with_other_questions():
    fake = SimpleNamespace(timetable_agent=SimpleNamespace(run=lambda **k: pytest.fail("no agent")))
    state = {"query": f"Connect my Google Calendar and {FEE}", "history": [], "identity": _student(),
             "questions": ["Connect my Google Calendar", FEE]}
    out = AuraChatGraph._n_personal_tools(fake, state)
    assert out.get("result") is None and out["questions"] == [FEE]
    assert "Connect your Google Calendar" in out["prefix_parts"][0]
    assert out["result_extras"]["action_required"]["type"] == "connect_required"


def test_profile_fast_path_does_not_hijack_a_compound_message():
    fake = SimpleNamespace()
    state = {"query": "What is my name? And the hostel fee?", "identity": _student(),
             "questions": ["What is my name?", "What is the hostel fee?"], "history": []}
    assert AuraChatGraph._n_profile_fast_path(fake, state).get("result") is None


# ── Retrieval + generation nodes ────────────────────────────────────────

class _Pipeline:
    def __init__(self):
        self.calls = []

    def get_context(self, query, history, **kw):
        self.calls.append(("single", query, kw))
        return {"chunks": [{"id": 1}], "context": "<context><doc id=\"1\">x</doc></context>",
                "sources": [], "standalone_query": query}

    def get_multi_context(self, questions, history, **kw):
        self.calls.append(("multi", list(questions), kw))
        return {"chunks": [{"id": 1}], "context": "<context><doc id=\"1\" q=\"1\">x</doc></context>",
                "sources": [], "standalone_query": " ".join(questions)}


def _rag_state(**extra):
    return {"query": "raw", "history": [], "query_type": "PUBLIC", "request_context": None, **extra}


def test_single_resolved_question_skips_the_legacy_rewrite():
    pipe = _Pipeline()
    AuraChatGraph._n_public_rag(SimpleNamespace(pipeline=pipe),
                                _rag_state(standalone_query="Resolved?", standalone_resolved=True))
    kind, q, kw = pipe.calls[0]
    assert (kind, q, kw["standalone"]) == ("single", "Resolved?", True)


def test_unresolved_single_question_keeps_the_original_call_shape():
    pipe = _Pipeline()
    AuraChatGraph._n_public_rag(SimpleNamespace(pipeline=pipe), _rag_state(standalone_query="raw"))
    kind, q, kw = pipe.calls[0]
    assert q == "raw" and "standalone" not in kw


def test_compound_questions_use_multi_retrieval_over_the_rag_subset():
    pipe = _Pipeline()
    AuraChatGraph._n_public_rag(
        SimpleNamespace(pipeline=pipe),
        _rag_state(questions=[FEE, DEAN, "my cgpa"], rag_questions=[FEE, DEAN], standalone_resolved=True))
    kind, qs, kw = pipe.calls[0]
    assert kind == "multi" and qs == [FEE, DEAN] and kw["standalone"] is True


def test_explicit_title_hint_still_read_from_the_users_words():
    pipe = _Pipeline()
    AuraChatGraph._n_public_rag(
        SimpleNamespace(pipeline=pipe),
        {**_rag_state(query="According to 'Director General', who leads DAU?"),
         "standalone_query": "who leads DAU?", "standalone_resolved": True})
    assert pipe.calls[0][2]["title_hint"] == "Director General"


def test_abstention_keeps_tool_answers_that_were_already_produced():
    class Empty(_Pipeline):
        def get_context(self, query, history, **kw):
            return {"chunks": [], "context": "<context>\n</context>", "sources": []}

    out = AuraChatGraph._n_public_rag(
        SimpleNamespace(pipeline=Empty()), _rag_state(prefix_parts=["TOOL ANSWER"]))
    assert out["result"]["answer"].startswith("TOOL ANSWER")


def test_transform_reuses_the_previous_answer_and_never_retrieves():
    pipe = SimpleNamespace(get_context=lambda *a, **k: pytest.fail("no retrieval"),
                           get_multi_context=lambda *a, **k: pytest.fail("no retrieval"))
    state = _rag_state(followup_type="transform_previous", questions=["Shorten it."],
                       history=[{"role": "assistant", "content": "Hostel fee is Rs. 60,000."}])
    out = AuraChatGraph._n_public_rag(SimpleNamespace(pipeline=pipe), state)
    assert "<previous_answer>" in out["rag_context"] and "60,000" in out["rag_context"]
    assert out["sources"] == [] and out.get("result") is None


class _Gen:
    def __init__(self, answer="1. Fee. [1]\n2. Dean. [1]"):
        self.kwargs, self.answer = None, answer

    def generate(self, **kwargs):
        self.kwargs = kwargs
        if kwargs.get("on_delta"):
            kwargs["on_delta"](self.answer)
        return self.answer


def _gen_state(**extra):
    return {"query": "raw", "history": [], "query_type": "PUBLIC", "request_context": None,
            "rag_context": '<context><doc id="1">x</doc></context>', "retrieval_result": {
                "standalone_query": "S", "plan": {}, "citation_map": {}},
            "sources": [], **extra}


def test_generate_passes_all_questions_and_prepends_tool_answers_to_reply_and_stream():
    gen, streamed = _Gen(), []
    state = _gen_state(questions=[FEE, DEAN], prefix_parts=["TOOL"], on_delta=streamed.append,
                       result_extras={"action_required": {"type": "connect_required"}, "is_personal_data": True})
    out = AuraChatGraph._n_generate(SimpleNamespace(generator=gen), state)
    assert gen.kwargs["questions"] == [FEE, DEAN]
    assert streamed[0] == "TOOL\n\n"                      # shown before generation starts
    assert out["result"]["answer"].startswith("TOOL\n\n1. Fee.")
    assert out["result"]["action_required"]["type"] == "connect_required"
    assert out["result"]["is_personal_data"] is True


def test_generate_single_question_call_shape_is_unchanged():
    gen = _Gen("Answer. [1]")
    AuraChatGraph._n_generate(SimpleNamespace(generator=gen), _gen_state(questions=["Q"]))
    assert "questions" not in gen.kwargs and "followup_type" not in gen.kwargs
    assert gen.kwargs["query"] == "S"


def test_personal_data_answers_see_the_resolved_follow_up():
    gen = _Gen("Your CGPA is 8.5.")
    AuraChatGraph._n_generate(
        SimpleNamespace(generator=gen),
        _gen_state(query_type="PERSONAL", rag_context="", erp_context="CGPA: 8.5", is_personal=True,
                   standalone_query="What was my CGPA last semester?"))
    assert gen.kwargs["query"] == "What was my CGPA last semester?"


def test_transform_flag_reaches_the_generator():
    gen = _Gen("Short.")
    AuraChatGraph._n_generate(
        SimpleNamespace(generator=gen),
        _gen_state(followup_type="transform_previous",
                   rag_context="<context><previous_answer>x</previous_answer></context>"))
    assert gen.kwargs["followup_type"] == "transform_previous"


# ── End to end through the real compiled graph ──────────────────────────

def _graph(understand, classify, pipeline, generator):
    g = AuraChatGraph.__new__(AuraChatGraph)
    g.guardrail = _guard(lambda q: Verdict.SAFE)
    g.wellness = SimpleNamespace(check=lambda *a, **k: False)
    g.understander = SimpleNamespace(understand=understand)
    g.classifier = SimpleNamespace(classify=classify)
    g.pipeline, g.generator = pipeline, generator
    g._graph = g._build_graph()
    return g


def test_e2e_two_questions_in_one_prompt_get_separate_retrieval_and_one_answer():
    pipe, gen = _Pipeline(), _Gen()
    und = Understanding("raw", (FEE, DEAN), "new", True, True)
    g = _graph(lambda *a, **k: und, lambda q, history=None: PUBLIC, pipe, gen)
    out = g.chat(f"{FEE} Also, {DEAN}")
    assert pipe.calls[0][:2] == ("multi", [FEE, DEAN])
    assert gen.kwargs["questions"] == [FEE, DEAN]
    assert out["answer"].startswith("1. Fee.")


def test_e2e_long_follow_up_without_pronoun_is_resolved_before_retrieval_and_classification():
    """The old gate skipped queries of 9+ words with no listed pronoun."""
    resolved = "What are the eligibility criteria for B.Tech ICT under the Gujarat quota category?"
    seen_cls, pipe, gen = [], _Pipeline(), _Gen("Criteria. [1]")
    und = Understanding("raw", (resolved,), "follow_up", True, True)
    g = _graph(lambda *a, **k: und, lambda q, history=None: seen_cls.append(q) or PUBLIC, pipe, gen)
    g.chat("And what are the eligibility criteria under the Gujarat quota category for students?",
           history=[{"role": "user", "content": "Tell me about B.Tech ICT"},
                    {"role": "assistant", "content": "B.Tech ICT is ..."}])
    assert seen_cls == [resolved]
    kind, q, kw = pipe.calls[0]
    assert (kind, q, kw["standalone"]) == ("single", resolved, True)


def test_e2e_rework_request_answers_from_previous_answer_without_retrieval():
    und = Understanding("shorter", ("Shorten the previous answer about hostel fees.",), "transform_previous", True, True)
    pipe = SimpleNamespace(get_context=lambda *a, **k: pytest.fail("no retrieval"),
                           get_multi_context=lambda *a, **k: pytest.fail("no retrieval"))
    gen = _Gen("Hostel fee: Rs. 60,000.")
    g = _graph(lambda *a, **k: und, lambda q, history=None: PUBLIC, pipe, gen)
    out = g.chat("make that shorter", history=[
        {"role": "user", "content": "hostel fee?"},
        {"role": "assistant", "content": "The annual hostel fee is Rs. 60,000 payable in two instalments. [1]"}])
    assert "<previous_answer>" in gen.kwargs["context"]
    assert gen.kwargs["followup_type"] == "transform_previous"
    assert out["answer"] == "Hostel fee: Rs. 60,000."
