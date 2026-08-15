"""
Covers EcampusOrchestrator.run()'s "timetable_changed" flag -- set when a
timetable-mutating tool (update_my_timetable, undo_timetable_change,
set_my_cohort, save_my_elective_selections) actually applied this turn, as
opposed to just previewing a change or erroring. This flag is what lets
chat_routes.py emit a "timetable-changed" SSE event, which
use-aura-chat.ts turns into a same-tab "aura:timetable-changed" window
event that use-timetable.ts listens for to refetch the dashboard card.

_call_llm is mocked (two calls: the tool-choice call, then the follow-up
answer call) so these stay fast and don't need a live inference node.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.ecampus.orchestrator import EcampusOrchestrator

IDENTITY = {"erp_id": "202301234", "role": "student", "dept": "ICT"}


def _tool_call(call_id: str, name: str, arguments: str = "{}"):
    call = MagicMock()
    call.id = call_id
    call.function.name = name
    call.function.arguments = arguments
    return call


def _llm_response(tool_calls=None, content=""):
    msg = MagicMock()
    msg.tool_calls = tool_calls
    msg.content = content
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    return resp


def _run_with_tool_call(monkeypatch, tool_name, tool_result, arguments="{}"):
    orch = EcampusOrchestrator()
    tool_msg_response = _llm_response(
        tool_calls=[_tool_call("call_1", tool_name, arguments)]
    )
    follow_up_response = _llm_response(content="Done.")

    call_count = {"n": 0}

    def fake_call_llm(self, messages, tools=None, tool_choice=None):
        call_count["n"] += 1
        return tool_msg_response if call_count["n"] == 1 else follow_up_response

    with patch.object(EcampusOrchestrator, "_call_llm", fake_call_llm), \
         patch(
             "pipeline.ecampus.orchestrator.MERGED_TOOL_REGISTRY",
             {tool_name: MagicMock(allowed_roles=["student"], handler=lambda identity, **kw: tool_result)},
         ), \
         patch.object(orch, "_tool_schemas", return_value=[{"type": "function", "function": {"name": tool_name}}]):
        return orch.run(query="add IT302 Monday 5pm", identity=IDENTITY, tool_scope="personal_actions")


def test_applied_update_sets_timetable_changed():
    result = _run_with_tool_call(
        None, "update_my_timetable", {"status": "applied", "slot": {}},
    )
    assert result.get("timetable_changed") is True


def test_saved_elective_selection_sets_timetable_changed():
    # save_my_elective_selections uses "saved"/"reset", not "applied" --
    # both must count as success.
    result = _run_with_tool_call(
        None, "save_my_elective_selections", {"status": "saved", "timetable": {}},
    )
    assert result.get("timetable_changed") is True


def test_updated_cohort_sets_timetable_changed():
    result = _run_with_tool_call(
        None, "set_my_cohort", {"status": "updated", "cohort": {}},
    )
    assert result.get("timetable_changed") is True


def test_confirmation_required_does_not_set_timetable_changed():
    # First call of a confirm-gated tool -- nothing actually applied yet.
    result = _run_with_tool_call(
        None, "update_my_timetable", {"status": "confirmation_required", "preview": {}},
    )
    assert "timetable_changed" not in result


def test_tool_error_does_not_set_timetable_changed():
    result = _run_with_tool_call(
        None, "update_my_timetable", {"error": "Slot conflicts with an existing class."},
    )
    assert "timetable_changed" not in result


def test_read_only_tool_does_not_set_timetable_changed():
    result = _run_with_tool_call(
        None, "get_my_timetable", {"status": "ok", "timetable": []},
    )
    assert "timetable_changed" not in result
