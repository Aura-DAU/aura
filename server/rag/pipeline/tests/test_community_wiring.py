"""
Offline tests for PersonalDataIntentRouter three-way classification and
AuraChatGraph public-KB wiring (intent_router → EcampusOrchestrator with
community + domain KB tools).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAG_DIR = Path(__file__).resolve().parent.parent.parent  # server/rag
for p in (str(RAG_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline.ecampus.intent_router import PersonalDataIntentRouter
from pipeline.ecampus.tool_registry import (
    COMMUNITY_TOOL_NAMES,
    KB_DOMAIN_TOOL_NAMES,
    PUBLIC_KB_TOOL_NAMES,
    community_tools_for_role,
    public_kb_tools_for_role,
    tools_for_role,
)
from pipeline.ecampus.orchestrator import EcampusOrchestrator


class _StubCompletions:
    def __init__(self, content: str, raises: bool = False):
        self._content = content
        self._raises = raises
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._raises:
            raise RuntimeError("endpoint unreachable")

        class _Msg:
            content = self._content

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


def _router_returning(content: str, raises: bool = False) -> PersonalDataIntentRouter:
    router = PersonalDataIntentRouter()
    completions = _StubCompletions(content, raises=raises)
    router.client = type(
        "_StubClient",
        (),
        {"chat": type("_Chat", (), {"completions": completions})()},
    )()
    router._stub = completions
    return router


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("PERSONAL_DATA", "PERSONAL_DATA"),
        ("COMMUNITY", "COMMUNITY"),
        ("PUBLIC_KB", "COMMUNITY"),
        ("GENERAL", "GENERAL"),
        ("community", "COMMUNITY"),
        ("something else", "GENERAL"),
    ],
)
def test_intent_router_classify_parsing(raw, expected):
    assert _router_returning(raw).classify("q") == expected


def test_intent_router_fails_toward_general():
    assert _router_returning("", raises=True).classify("my CGPA") == "GENERAL"
    assert _router_returning("", raises=True).is_community_query("clubs") is False
    assert _router_returning("", raises=True).is_personal_data_query("cgpa") is False


def test_intent_router_prompt_includes_public_kb_domains():
    prompt = PersonalDataIntentRouter().system_prompt
    assert "COMMUNITY" in prompt
    assert "PERSONAL_DATA" in prompt
    assert "GENERAL" in prompt
    assert "Who is Aditya Tatu?" in prompt
    assert "faculty" in prompt.lower()
    assert "academic calendar" in prompt.lower() or "calendar" in prompt.lower()
    assert "placement" in prompt.lower()
    assert "club" in prompt.lower()


def test_community_tools_for_role_excludes_personal_erp():
    student = {t.name for t in community_tools_for_role("student")}
    assert student <= COMMUNITY_TOOL_NAMES
    assert "get_club_members" in student
    assert "get_cgpa" not in student
    assert "lookup_faculty_profile" not in student

    faculty = {t.name for t in community_tools_for_role("faculty")}
    assert "search_faculty_committees" in faculty
    assert "get_cgpa" not in faculty
    assert "get_cgpa" in {t.name for t in tools_for_role("student")}


def test_public_kb_tools_include_community_and_domain():
    assert COMMUNITY_TOOL_NAMES <= PUBLIC_KB_TOOL_NAMES
    assert KB_DOMAIN_TOOL_NAMES <= PUBLIC_KB_TOOL_NAMES
    assert "lookup_faculty_profile" in PUBLIC_KB_TOOL_NAMES
    assert "lookup_academic_calendar" in PUBLIC_KB_TOOL_NAMES
    assert "get_cgpa" not in PUBLIC_KB_TOOL_NAMES

    student = {t.name for t in public_kb_tools_for_role("student")}
    assert "get_club_members" in student
    assert "lookup_faculty_profile" in student
    assert "lookup_placement_careers_info" in student
    assert "get_cgpa" not in student
    assert student <= PUBLIC_KB_TOOL_NAMES


def test_orchestrator_public_kb_scope_schemas_exclude_erp():
    orch = EcampusOrchestrator()
    for scope in ("community", "public_kb"):
        names = {
            s["function"]["name"]
            for s in orch._tool_schemas("student", tool_scope=scope)
        }
        assert names <= PUBLIC_KB_TOOL_NAMES
        assert "get_cgpa" not in names
        assert "search_student_clubs" in names
        assert "lookup_faculty_profile" in names
        assert "lookup_academic_calendar" in names


def test_aura_chat_graph_community_node_invokes_orchestrator(monkeypatch):
    from pipeline.aura_chat_graph import AuraChatGraph, SimpleIdentity

    def _fake_init(self):
        self.intent_router = SimpleNamespace(
            classify=lambda q: "COMMUNITY" if "club" in q.lower() or "tatu" in q.lower() else "GENERAL",
        )
        self.ecampus_orchestrator = SimpleNamespace(
            run=lambda **kwargs: {
                "answer": f"orchestrated:{kwargs['tool_scope']}:{kwargs['identity']['role']}",
                "sources": ["club.md"],
            }
        )

    monkeypatch.setattr(AuraChatGraph, "__init__", _fake_init)
    graph = AuraChatGraph()
    state = {
        "query": "Who is the convenor of the Programming Club?",
        "history": [],
        "identity": SimpleIdentity(erp_id="S1", role="student", dept="ICT"),
        "request_context": None,
        "result": None,
    }
    out = graph._n_community_tools(state)
    assert out["result"]["answer"] == "orchestrated:public_kb:student"
    assert out["result"]["sources"] == ["club.md"]
    assert out["result"]["is_personal_data"] is False

    # Faculty who-is also routes through the same public-KB path.
    who_state = {
        "query": "Who is Aditya Tatu?",
        "history": [],
        "identity": SimpleIdentity(erp_id="S1", role="student"),
        "request_context": None,
        "result": None,
    }
    who_out = graph._n_community_tools(who_state)
    assert who_out["result"]["answer"] == "orchestrated:public_kb:student"


def test_aura_chat_graph_community_skips_guests_and_general(monkeypatch):
    from pipeline.aura_chat_graph import AuraChatGraph, SimpleIdentity

    calls = []

    def _fake_init(self):
        self.intent_router = SimpleNamespace(classify=lambda q: "COMMUNITY")
        self.ecampus_orchestrator = SimpleNamespace(
            run=lambda **kwargs: calls.append(kwargs) or {"answer": "x", "sources": []}
        )

    monkeypatch.setattr(AuraChatGraph, "__init__", _fake_init)
    graph = AuraChatGraph()

    guest_state = {
        "query": "What clubs for music?",
        "history": [],
        "identity": SimpleIdentity(erp_id=None, role="guest"),
        "result": None,
    }
    assert graph._n_community_tools(guest_state).get("result") is None
    assert calls == []

    graph.intent_router = SimpleNamespace(classify=lambda q: "GENERAL")
    student_state = {
        "query": "hello there vaguely",
        "history": [],
        "identity": SimpleIdentity(erp_id="S1", role="student"),
        "result": None,
    }
    assert graph._n_community_tools(student_state).get("result") is None
    assert calls == []
