"""
AuraChatGraph — LangGraph implementation of the Agent Orchestrator.

The architecture doc (`AURA System Architecture and Working.pdf`, §6)
describes the Agent Orchestrator as a LangGraph-driven state machine that
decides which information to collect (guardrails → classification →
access control → retrieval/ERP fetch → generation) before ever calling the
language model. `pipeline.aura_chat.AuraChat` implemented that same 7-step
flow as a hand-written sequence of `if`/`return` statements; this module
reimplements it as an explicit `StateGraph` with one node per pipeline
stage and conditional edges for every early-exit branch (unsafe query,
wellness flag, greeting, guest-on-personal-path, strict-guardrail failure,
access-denied, empty retrieval).

Every node delegates to the *same* collaborator objects AuraChat uses
(`QueryGuardrail`, `WellnessGuardrail`, `PersonalQueryClassifier`,
`AccessControlGate`, `AuditLog`, `RetrievalPipeline`, `AnswerGenerator`) —
this file only reorganises the control flow into a graph, it does not
reimplement any of the underlying business logic.

`rag.py` (the `AURA` facade used by the FastAPI layer) instantiates this
class instead of `AuraChat` directly. `AuraChat` itself is left in place
unmodified as the reference implementation / fallback.
"""

import re
from typing import Optional, TypedDict, Any

from langgraph.graph import StateGraph, END

from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
from pipeline.generation.answer_generator import (
    AnswerGenerator,
    filter_sources_by_citations,
    log_soft_failure,
)
from pipeline.guardrails.query_guardrail import (
    OFF_TOPIC_RESPONSE,
    QueryGuardrail,
    Verdict,
)
from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
from pipeline.latency_tracker import track_segment

from erp_connector import ERPConnector
from erp_context_builder import ERPContextBuilder
from access_control import AccessControlGate, AccessDecision, resolve_effective_role
from audit_log import AuditLog
from personal_query_classifier import PersonalQueryClassifier

from pipeline.aura_chat import (
    GENERIC_DENIAL,
    ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE,
    RETRIEVAL_FAILURE_RESPONSE,
    PERSONAL_DATA_SYSTEM_ADDENDUM,
    is_greeting_or_meta,
)
from pipeline.ecampus.intent_router import PersonalDataIntentRouter
from pipeline.ecampus.orchestrator import (
    EcampusOrchestrator,
    _required_calendar_tool,
    _is_calendar_unsync_intent,
    _is_timetable_edit_confirmation,
    _is_timetable_edit_intent,
)
from api.request_context import RequestContext


# Keyword gate for the in-chat calendar-sync path (_n_personal_tools). Kept
# deliberately narrow: only calendar/schedule *sync* requests are routed to the
# tool agent, so ordinary personal lookups ("what's my timetable today",
# "my CGPA") never leave the curated ERP path. Over-triggering is safe — the
# actions scope exposes no ERP tools, so a non-matching query calls no tool and
# falls through — but keeping it tight avoids a needless extra LLM call.
_CALENDAR_KEYWORD_RE = re.compile(r"\bcalendar\b", re.IGNORECASE)
_SCHEDULE_ACTION_RE = re.compile(
    r"\b(add|sync|put|export|save)\b.{0,40}\b(schedule|timetable|classes|class)\b"
    r"|\b(schedule|timetable|classes)\b.{0,20}\bcalendar\b",
    re.IGNORECASE,
)
_CALENDAR_CONNECT_RE = re.compile(
    r"\b(?:connect|link)\b.{0,30}\b(?:my\s+)?(?:google\s+)?calendar\b"
    r"|\b(?:google\s+)?calendar\b.{0,30}\b(?:connect|link)\b",
    re.IGNORECASE,
)
_CLUB_OFFICE_BEARER_RE = re.compile(
    r"\b(conven(?:er|or)|coordinator|office[ -]?bearer|"
    r"deputy[ -]?conven(?:er|or)|dy\.?[ -]?conven(?:er|or)|"
    r"faculty mentor|club email)\b",
    re.IGNORECASE,
)
_CLUB_CONTEXT_RE = re.compile(r"\b(club|sbg|committee)\b", re.IGNORECASE)


def _is_calendar_sync_intent(query: str) -> bool:
    return bool(_CALENDAR_KEYWORD_RE.search(query) or _SCHEDULE_ACTION_RE.search(query))


def _is_calendar_connect_intent(query: str) -> bool:
    return bool(_CALENDAR_CONNECT_RE.search(query))


def _is_club_office_bearer_intent(query: str) -> bool:
    """Route published club contacts to the C_DCs-aware lookup path.

    This is intentionally narrower than all club requests: only questions that
    ask for office-bearers bypass the general-purpose intent classifier, whose
    unavailable/invalid fallback is GENERAL and otherwise sends the request to
    the legacy RAG path.
    """
    return bool(_CLUB_CONTEXT_RE.search(query) and _CLUB_OFFICE_BEARER_RE.search(query))


class SimpleIdentity:
    def __init__(self, d=None, **kwargs):
        if d is None:
            d = kwargs
        if isinstance(d, dict):
            self.erp_id = d.get("erp_id") or d.get("erpId")
            self.role = d.get("role", "student")
            self.dept = d.get("dept") or d.get("department") or d.get("branch") or "ICT"
            self.email = d.get("email")
            self.full_name = d.get("full_name") or d.get("fullName") or d.get("name")
            self.roll_number = d.get("roll_number") or d.get("rollNumber") or self.erp_id
            self.program = d.get("program") or d.get("programme") or "B.Tech. (ICT)"
            self.branch = d.get("branch") or self.dept
            self.current_year = d.get("current_year") or d.get("currentYear") or 3
            self.current_sem = d.get("current_sem") or d.get("currentSem") or 5
        else:
            self.erp_id = getattr(d, "erp_id", None)
            self.role = getattr(d, "role", "student")
            self.dept = getattr(d, "dept", None)
            self.email = getattr(d, "email", None)
            self.full_name = getattr(d, "full_name", None)
            self.roll_number = getattr(d, "roll_number", None) or self.erp_id
            self.program = getattr(d, "program", None)
            self.branch = getattr(d, "branch", None) or self.dept
            self.current_year = getattr(d, "current_year", None)
            self.current_sem = getattr(d, "current_sem", None)


class AuraState(TypedDict, total=False):
    query: str
    history: list
    identity: Any
    request_context: RequestContext
    academic_scope: Any
    display_profile: Any
    on_delta: Any  # token-streaming callback, threaded straight to the generator
    summary: Optional[str]  # rolling conversation memory (pipeline.memory)

    query_type: Optional[str]
    classification: dict
    user_role: str
    ecampus_intent: Optional[str]  # PersonalDataIntentRouter verdict, computed once

    target_erp_id: Optional[str]
    access_result: Any
    erp_context: str
    is_personal: bool

    retrieval_result: dict
    chunks: list
    rag_context: str
    sources: list

    answer: str
    result: Optional[dict]  # set by any node that wants to short-circuit


class AuraChatGraph:
    """Drop-in replacement for AuraChat.chat() — same call signature and
    return contract, LangGraph state machine underneath."""

    def __init__(self):
        self.pipeline = RetrievalPipeline()
        self.generator = AnswerGenerator()
        self.guardrail = QueryGuardrail()
        self.wellness = WellnessGuardrail()

        erp = ERPConnector()
        self.classifier = PersonalQueryClassifier()
        self.erp_connector = erp
        self.context_builder = ERPContextBuilder()
        self.access_gate = AccessControlGate(erp)
        self.audit_log = AuditLog()
        self.intent_router = PersonalDataIntentRouter()
        self.ecampus_orchestrator = EcampusOrchestrator()

        self._graph = self._build_graph()

    # ── Graph construction ──────────────────────────────────────────────

    def _build_graph(self):
        graph = StateGraph(AuraState)

        graph.add_node("safety_guardrail", self._n_safety_guardrail)
        graph.add_node("wellness_check", self._n_wellness_check)
        graph.add_node("greeting_check", self._n_greeting_check)
        graph.add_node("profile_fast_path", self._n_profile_fast_path)
        graph.add_node("community_tools", self._n_community_tools)
        graph.add_node("personal_tools", self._n_personal_tools)
        graph.add_node("classify", self._n_classify)
        graph.add_node("guest_gate", self._n_guest_gate)
        graph.add_node("strict_guardrail", self._n_strict_guardrail)
        graph.add_node("personal_data", self._n_personal_data)
        graph.add_node("public_rag", self._n_public_rag)
        graph.add_node("generate", self._n_generate)

        graph.set_entry_point("safety_guardrail")

        # Every node whose logic can short-circuit checks state["result"];
        # if it's set, the query is done and we route straight to END
        # instead of falling through to the next pipeline stage. This is
        # the graph-native equivalent of AuraChat's early `return`s.
        def route_or(next_node: str):
            def _route(state: AuraState):
                return END if state.get("result") is not None else next_node
            return _route

        graph.add_conditional_edges("safety_guardrail", route_or("wellness_check"))
        graph.add_conditional_edges("wellness_check", route_or("greeting_check"))
        graph.add_conditional_edges("greeting_check", route_or("profile_fast_path"))
        graph.add_conditional_edges("profile_fast_path", route_or("community_tools"))
        graph.add_conditional_edges("community_tools", route_or("personal_tools"))
        graph.add_conditional_edges("personal_tools", route_or("classify"))
        graph.add_conditional_edges("classify", route_or("guest_gate"))
        graph.add_conditional_edges("guest_gate", route_or("strict_guardrail"))
        graph.add_conditional_edges("strict_guardrail", route_or("personal_data"))
        graph.add_conditional_edges("personal_data", route_or("public_rag"))
        graph.add_conditional_edges("public_rag", route_or("generate"))
        graph.add_edge("generate", END)

        return graph.compile()

    # ── Nodes (each mirrors one guarded step of AuraChat.chat()) ────────

    def _n_safety_guardrail(self, state: AuraState) -> AuraState:
        with track_segment("guardrail_time"):
            verdict = self.guardrail.classify(state["query"])
        # None = classifier unreachable. Fails OPEN on the public RAG path,
        # matching is_safe(); the personal-data path re-checks with
        # is_safe_strict() further down the graph, which fails closed.
        if verdict is Verdict.UNSAFE:
            state["result"] = {
                "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                "sources": [],
            }
        elif verdict is Verdict.OFF_TOPIC:
            state["result"] = {
                "answer": OFF_TOPIC_RESPONSE,
                "sources": [],
            }
        return state

    def _n_wellness_check(self, state: AuraState) -> AuraState:
        if self.wellness.check(state["query"]):
            state["result"] = {
                "answer": self.wellness.get_response(),
                "sources": [],
                "is_personal_data": False,
            }
        return state

    def _n_greeting_check(self, state: AuraState) -> AuraState:
        query = state["query"]
        if not is_greeting_or_meta(query):
            return state

        q = re.sub(r'[?.!,]+$', '', query.strip()).lower().strip()
        words = q.split()
        help_words = {"what can you do", "help", "menu", "intro", "introduce yourself"}
        who_words = {"who are you", "who is aura", "what is aura"}

        if q in help_words or any(w in help_words for w in words):
            ans = (
                "I can help you with a wide range of questions about Dhirubhai Ambani University, including:\n"
                "- **Admissions & Academics**: Program details, fee structures, eligibility criteria, and academic policies.\n"
                "- **Campus & Facilities**: Hostel rules, dining details, medical SOPs, and general guidelines.\n"
                "- **Personal ERP Records**: You can check your CPI/CGPA, attendance, and course grades securely.\n"
                "- **Calendar Actions**: I can help you schedule appointments or check event dates.\n\n"
                "How can I assist you today?"
            )
        elif q in who_words or any(w in who_words for w in words):
            ans = (
                "I am AURA, the official AI assistant for Dhirubhai Ambani University (DAU). "
                "I am here to help you navigate university life, policies, academics, admissions, "
                "and connect you with your personal academic data from the ERP system. How can I help you today?"
            )
        else:
            ans = (
                "Hello! I am AURA, the official AI assistant for Dhirubhai Ambani University (DAU). "
                "I can help you with questions about admissions, academics, faculty, courses, campus life, "
                "and your personal student records (like CGPA, grades, and attendance). How can I assist you today?"
            )

        state["result"] = {"answer": ans, "sources": [], "is_personal_data": False}
        return state

    def _n_profile_fast_path(self, state: AuraState) -> AuraState:
        """Answer pure identity questions without RAG/ERP (mirrors AuraChat)."""
        from personal_query_classifier import is_pure_profile_query

        query = state["query"]
        identity = state.get("identity")
        if not identity or not is_pure_profile_query(query):
            return state
        if getattr(identity, "role", None) in (None, "guest"):
            return state

        name = getattr(identity, "full_name", None) or "Student"
        roll = getattr(identity, "roll_number", None) or getattr(identity, "erp_id", "N/A")
        scope = state.get("academic_scope")
        prog = (
            (getattr(scope, "programme_id", None) if scope else None)
            or getattr(identity, "program", None)
            or getattr(identity, "programme", None)
            or "your programme"
        )
        branch = (
            getattr(identity, "dept", None)
            or getattr(identity, "branch", None)
            or (getattr(scope, "department_id", None) if scope else None)
            or "your department"
        )
        sem = (
            getattr(identity, "current_sem", None)
            or (getattr(scope, "current_semester", None) if scope else None)
        )
        email = getattr(identity, "email", None) or (
            f"{str(roll).lower()}@dau.ac.in" if roll and roll != "N/A" else None
        )

        q_lower = query.lower()
        if "name" in q_lower or "who am i" in q_lower:
            ans = f"You are **{name}** (Roll Number: `{roll}`)."
        elif "roll" in q_lower or ("id" in q_lower and "student" in q_lower):
            ans = f"Your roll number is `{roll}`."
        elif "email" in q_lower:
            ans = f"Your official university email is `{email}`." if email else (
                f"Your roll number is `{roll}`; use `{str(roll).lower()}@dau.ac.in` if that is your institutional mailbox."
            )
        elif "branch" in q_lower or "dept" in q_lower:
            ans = f"You are in the **{branch}** department."
        elif "semester" in q_lower:
            if sem is not None:
                ans = f"You are currently in **Semester {sem}** of the {prog} program."
            else:
                ans = f"You are enrolled in the **{prog}** program ({branch})."
        else:
            sem_bit = f"**Semester {sem}** of " if sem is not None else ""
            ans = (
                f"You are **{name}** (Roll Number: `{roll}`), currently enrolled in "
                f"{sem_bit}the **{prog}** program in the **{branch}** department."
            )
        state["result"] = {"answer": ans, "sources": [], "is_personal_data": True}
        return state

    def _n_community_tools(self, state: AuraState) -> AuraState:
        # Clubs / SBG / faculty ToR / domain KB skills → EcampusOrchestrator
        # with public KB tools only. Guests and non-COMMUNITY queries fall
        # through to classify → public RAG (or the personal ERP path).
        # Personal ERP tools are never exposed on this branch.
        identity = state.get("identity")
        if not identity or getattr(identity, "role", None) in (None, "guest"):
            return state

        # Google Calendar actions belong to the personal MCP path, not the
        # public academic-calendar KB path. This node runs first, so relying on
        # the intent model to preserve that distinction can end the graph with
        # public-KB prose before _n_personal_tools gets a chance to call MCP.
        if getattr(identity, "role", None) == "student" and (
            _is_calendar_connect_intent(state["query"])
            or _is_calendar_unsync_intent(state["query"])
            or _is_timetable_edit_intent(state["query"])
            or _is_timetable_edit_confirmation(
                state["query"],
                state.get("history") or [],
            )
            or _required_calendar_tool(
                state["query"],
                state.get("history") or [],
            )
        ):
            state["ecampus_intent"] = "PERSONAL_DATA"
            return state

        if _is_club_office_bearer_intent(state["query"]):
            intent = "COMMUNITY"
        else:
            with track_segment("community_intent_time"):
                intent = self.intent_router.classify(state["query"])
        # Stash the verdict so _n_personal_tools can reuse it without a second
        # classifier round-trip.
        state["ecampus_intent"] = intent
        if intent != "COMMUNITY":
            return state

        tool_role = identity.role if identity.role in ("student", "faculty") else None
        if tool_role is None:
            # Broad JWT role is student|faculty|admin; map elevated faculty
            # effective roles if present on request_context.
            request_context = state.get("request_context")
            effective = getattr(request_context, "effective_role", None) or ""
            if effective.startswith("faculty") or effective in (
                "dean_faculty", "dean_academic", "dean_students", "superadmin",
            ):
                tool_role = "faculty"
            elif effective == "student":
                tool_role = "student"
            else:
                return state

        identity_payload = {
            "erp_id": identity.erp_id,
            "role": tool_role,
            "dept": getattr(identity, "dept", None),
        }
        try:
            with track_segment("community_orchestrator_time"):
                result = self.ecampus_orchestrator.run(
                    query=state["query"],
                    identity=identity_payload,
                    history=state.get("history") or [],
                    request_context=state.get("request_context"),
                    tool_scope="public_kb",
                )
        except Exception as exc:
            # Orchestrator/LLM failure must not kill the request — fall through
            # to classify → public RAG, which has its own error handling. This
            # is not itself a soft error, but it silently degrades a COMMUNITY
            # query to generic RAG, so it has to be attributable too.
            log_soft_failure(
                "AURA-GRAPH-003",
                "community_orchestrator",
                exc=exc,
                degraded_to="public_rag",
            )
            return state

        answer = (result.get("answer") or "").strip()
        if not answer:
            # Empty tool answer → let public RAG try instead of blank SSE.
            return state

        state["result"] = {
            "answer": answer,
            "sources": result.get("sources") or [],
            "is_personal_data": False,
        }
        return state

    def _n_personal_tools(self, state: AuraState) -> AuraState:
        # Signed-in students reach personal timetable writes and Google Calendar
        # actions here; guests get sign-in guidance. The actions scope exposes
        # only the student's timetable + calendar tools, never ERP reads.
        history = state.get("history") or []
        required_calendar_tool = _required_calendar_tool(state["query"], history)
        is_connect_intent = _is_calendar_connect_intent(state["query"])
        is_unsync_intent = _is_calendar_unsync_intent(state["query"])
        is_timetable_edit = _is_timetable_edit_intent(state["query"])
        is_timetable_confirmation = _is_timetable_edit_confirmation(
            state["query"], history
        )
        is_calendar_action = bool(
            required_calendar_tool or is_connect_intent or is_unsync_intent
        )
        is_personal_action = bool(
            is_calendar_action or is_timetable_edit or is_timetable_confirmation
        )
        identity = state.get("identity")

        if getattr(identity, "role", None) == "guest" and is_personal_action:
            state["result"] = {
                "answer": (
                    "Sign in with your DAU student account first, then ask me "
                    "again to manage your timetable."
                ),
                "sources": [],
                "is_personal_data": False,
            }
            return state

        if not identity or getattr(identity, "role", None) != "student":
            return state
        if (
            not _is_calendar_sync_intent(state["query"])
            and not is_unsync_intent
            and not required_calendar_tool
            and not is_timetable_edit
            and not is_timetable_confirmation
        ):
            return state

        # OAuth is initiated by the client-side connect CTA, not an MCP tool.
        # Returning it directly avoids relying on the model to infer a status
        # lookup before it can offer the student the OAuth flow.
        if is_connect_intent:
            state["result"] = {
                "answer": "Connect your Google Calendar to sync your timetable.",
                "sources": [],
                "is_personal_data": True,
                "action_required": {
                    "type": "connect_required",
                    "provider": "google_calendar",
                    "connect_path": "/settings/calendar",
                    "reason": "connect_google_calendar",
                    "message": "Connect your Google Calendar to sync your timetable.",
                },
            }
            return state

        # Removing events is a write, so the model is never asked to delete:
        # a first-time remove/unsync request gets a deterministic confirmation
        # prompt here, and the follow-up "yes" runs unsync_timetable_from_calendar
        # via _required_calendar_tool. The prompt keeps the "remove ... Google
        # Calendar ... proceed" phrasing that the confirmation gate keys on.
        if is_unsync_intent and not required_calendar_tool:
            state["result"] = {
                "answer": (
                    "This will remove the timetable events AURA added to your "
                    "Google Calendar. Confirm to proceed and I'll clear them."
                ),
                "sources": [],
                "is_personal_data": True,
            }
            return state

        identity_payload = {
            "erp_id": identity.erp_id,
            "role": "student",
            "dept": getattr(identity, "dept", None),
        }
        try:
            with track_segment("personal_tools_time"):
                result = self.ecampus_orchestrator.run(
                    query=state["query"],
                    identity=identity_payload,
                    history=history,
                    request_context=state.get("request_context"),
                    tool_scope="personal_actions",
                )
        except Exception as exc:
            # Never kill the request — degrade to the ERP/RAG path, but keep it
            # attributable (same policy as _n_community_tools).
            log_soft_failure(
                "AURA-GRAPH-004",
                "personal_tools_orchestrator",
                exc=exc,
                degraded_to="personal_data",
            )
            return state

        # Only commit if a tool actually ran. A no-tool run means the agent had
        # nothing to act on (e.g. the gate over-triggered) — let the curated ERP
        # path answer rather than surfacing the model's unfounded prose.
        if not result.get("used_tools"):
            return state

        answer = (result.get("answer") or "").strip()
        action_required = result.get("action_required")
        if not answer and not action_required:
            return state

        out: dict = {
            "answer": answer or (action_required or {}).get("message", ""),
            "sources": result.get("sources") or [],
            "is_personal_data": True,
        }
        if action_required:
            out["action_required"] = action_required
        state["result"] = out
        return state

    def _n_classify(self, state: AuraState) -> AuraState:
        classification = self.classifier.classify(state["query"])
        state["classification"] = classification
        state["query_type"] = classification["type"]
        return state

    def _n_guest_gate(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        if query_type in ("PERSONAL", "MIXED", "AGGREGATE"):
            request_context = state.get("request_context")
            user_role = request_context.effective_role if request_context else "guest"
            if user_role == "guest":
                state["result"] = {
                    "answer": GENERIC_DENIAL,
                    "sources": [],
                    "is_personal_data": False,
                }
        return state

    def _n_strict_guardrail(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        identity = state.get("identity")
        if query_type in ("PERSONAL", "MIXED", "AGGREGATE") and identity:
            with track_segment("guardrail_time"):
                is_safe_strict = self.guardrail.is_safe_strict(state["query"])
            if not is_safe_strict:
                state["result"] = {
                    "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                    "sources": [],
                    "is_personal_data": False,
                }
        return state

    def _n_personal_data(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        identity = state.get("identity")
        state.setdefault("erp_context", "")
        state.setdefault("is_personal", False)

        if query_type not in ("PERSONAL", "MIXED", "AGGREGATE") or not identity:
            return state

        classification = state["classification"]
        target_erp_id = self._resolve_target(classification["target"], identity)
        state["target_erp_id"] = target_erp_id

        access_result = self.access_gate.evaluate(
            identity=identity,
            query_intent=classification,
            target_identifier=target_erp_id,
        )
        state["access_result"] = access_result

        self.audit_log.record(
            erp_id=identity.erp_id,
            role=identity.role,
            query_text=state["query"],
            query_type=query_type.lower(),
            target_erp_id=target_erp_id,
            access_granted=(access_result.decision == AccessDecision.ALLOWED),
            denial_reason=access_result.reason if access_result.decision == AccessDecision.DENIED else None,
            erp_tables=classification.get("erp_fields", []),
            scope_context=getattr(access_result, "scope_context", None),
        )

        if access_result.decision == AccessDecision.DENIED:
            state["result"] = {"answer": GENERIC_DENIAL, "sources": [], "is_personal_data": False}
            return state

        if query_type == "AGGREGATE":
            course_code = (access_result.course_codes[0] if access_result.course_codes else None)
            try:
                erp_data = {"aggregate": self.erp_connector.get_class_aggregate(course_code) if course_code else {}}
            except Exception:
                import traceback; traceback.print_exc()
                state["result"] = {
                    "answer": "I'm having trouble reaching the student records system right now. Please try again in a moment.",
                    "sources": [], "is_personal_data": False,
                }
                return state
        else:
            # Fix PD-DEGRADE: this is the one DB-dependent step in this node
            # without its own error handling (audit_log.record above never
            # raises by design; access_gate.evaluate for "self" queries — the
            # overwhelming majority — makes no DB call at all). A transient
            # Postgres hiccup while fetching profile/cgpa/grades/attendance
            # used to propagate uncaught all the way to chat()'s top-level
            # except block, which returns "Sorry, I encountered an error
            # while generating a response" — a generation-stage message that
            # is actively misleading for what is really a data-fetch failure,
            # and specifically explains why this surfaced on personal
            # questions (profile/grades/attendance) more than public ones.
            try:
                erp_data = self._fetch_erp_data(
                    classification["erp_fields"],
                    target_erp_id,
                    access_result,
                    requester_erp_id=identity.erp_id,
                )
            except Exception:
                import traceback; traceback.print_exc()
                state["result"] = {
                    "answer": "I'm having trouble reaching the student records system right now. Please try again in a moment.",
                    "sources": [], "is_personal_data": False,
                }
                return state

        state["erp_context"] = self.context_builder.build(erp_data, identity, access_result)
        state["is_personal"] = True
        return state

    def _n_public_rag(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        state.setdefault("rag_context", "")
        state.setdefault("sources", [])

        if query_type not in ("PUBLIC", "MIXED", "AGGREGATE"):
            return state

        request_context = state.get("request_context")
        user_role = request_context.effective_role if request_context else "public"
        
        # Resolve institutional abbreviations (DADC -> Dance Club (DADC) at DAU)
        from institution_resolver import get_institution_resolver
        resolved_query = get_institution_resolver().resolve(state["query"])

        with track_segment("retrieval_time"):
            retrieval_result = self.pipeline.get_context(
                resolved_query,
                state["history"],
                user_role=user_role,
                academic_scope=state.get("academic_scope"),
                identity=state.get("identity"),
            )
        state["retrieval_result"] = retrieval_result
        state["chunks"] = retrieval_result.get("chunks", [])
        state["rag_context"] = retrieval_result.get("context", "")
        state["sources"] = retrieval_result.get("sources", [])

        if not state["chunks"] and query_type == "PUBLIC":
            reason = retrieval_result.get("abstention_reason")
            answer = (
                ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE
                if reason == "academic_scope_unavailable"
                else RETRIEVAL_FAILURE_RESPONSE
            )
            state["result"] = {
                "answer": answer,
                "sources": [],
                "is_personal_data": False,
            }
        return state

    def _n_generate(self, state: AuraState) -> AuraState:
        erp_context = state.get("erp_context", "")
        rag_context = state.get("rag_context", "")
        is_personal = state.get("is_personal", False)
        query_type = state["query_type"]
        retrieval_result = state.get("retrieval_result", {})
        request_context = state.get("request_context")
        user_role = request_context.effective_role if request_context else "public"

        from privacy_filter import ResponsePrivacyFilter
        privacy_filter = ResponsePrivacyFilter(user_role=user_role)

        combined_context = "\n\n".join(filter(None, [erp_context, rag_context]))
        combined_context = privacy_filter.sanitize_retrieved_context(combined_context)

        has_rag = query_type in ("PUBLIC", "MIXED") and bool(rag_context)

        with track_segment("generation_time"):
            # on_delta / summary are stored on state by chat() and must be
            # forwarded — without them /chat/stream silently buffers, and the
            # rolling conversation digest never reaches the generator (so the
            # token budget under-counts what the prompt would include once
            # memory is wired).
            answer = self.generator.generate(
                query=retrieval_result.get("corrected_query", state["query"]) if has_rag else state["query"],
                context=combined_context,
                plan=retrieval_result.get("plan") if has_rag else None,
                history=state.get("history") or [],
                profile=state.get("display_profile"),
                system_addendum=PERSONAL_DATA_SYSTEM_ADDENDUM if is_personal else None,
                on_delta=state.get("on_delta"),
                on_profile_update=state.get("on_profile_update"),
                profile_erp_id=state.get("identity").erp_id if state.get("identity") else None,
                summary=(state.get("summary") or None),
                tracking_flags=request_context.tracking_flags if request_context else None,
            )

        # Apply post-generation privacy filter
        answer = privacy_filter.filter_response_text(answer, query=state["query"])

        state["result"] = {
            "answer": answer,
            "sources": filter_sources_by_citations(
                state.get("sources", []),
                retrieval_result.get("citation_map", {}),
                answer,
            ),
            "is_personal_data": is_personal,
        }
        return state

    # ── Helpers (ported unchanged from AuraChat) ────────────────────────

    def _resolve_target(self, target_label: Optional[str], identity) -> Optional[str]:
        if not target_label or target_label == "self":
            return identity.erp_id
        if target_label and target_label[:3].isdigit():
            return target_label
        result = self.erp_connector.find_student_by_name(target_label)
        return result["roll_number"] if result else None

    def _fetch_erp_data(
        self,
        fields: list,
        roll_number: Optional[str],
        access_result,
        requester_erp_id: Optional[str] = None,
    ) -> dict:
        if not roll_number:
            return {}
        data = {}
        scope = getattr(access_result, "scope_type", None)
        course_scope = (access_result.course_codes[0] if access_result.course_codes else None)

        # Course-scoped access: only that course's grades/attendance — never
        # overall CGPA or full profile (would overshare vs the teaching link).
        if scope == "course":
            if "grades" in fields:
                data["grades"] = self.erp_connector.get_grades(roll_number, course_code=course_scope)
            if "attendance" in fields:
                data["attendance"] = self.erp_connector.get_attendance(roll_number, course_code=course_scope)
            return data

        if "profile" in fields:
            data["profile"] = self.erp_connector.get_student_profile(roll_number)
        if "cgpa" in fields:
            data["cgpa"] = self.erp_connector.get_cgpa(roll_number)
        if "grades" in fields:
            data["grades"] = self.erp_connector.get_grades(roll_number, course_code=course_scope)
        if "attendance" in fields:
            data["attendance"] = self.erp_connector.get_attendance(roll_number, course_code=course_scope)
        if "advisees" in fields and scope in ("advisee", "all", "batch") and requester_erp_id:
            data["advisees"] = self.erp_connector.get_advisees(requester_erp_id)
        if "courses" in fields and requester_erp_id:
            data["courses"] = self.erp_connector.get_faculty_courses(requester_erp_id)
        return data

    # ── Public entrypoint (same signature/contract as AuraChat.chat) ────

    def _answer_profile(self, state: AuraState) -> dict | None:
        scope = state.get("academic_scope")
        display_profile = state.get("display_profile") or {}
        if not scope:
            return display_profile or None
        profile = {
            "role": "student",
            "programme": scope.programme_id,
            "degree_level": scope.degree_level,
            "admission_year": scope.admission_year,
            "current_semester": scope.current_semester,
        }
        if scope.branch_id:
            profile["branch"] = scope.branch_id
        return profile

    def chat(self, query, history=None, identity=None, display_profile=None, on_delta=None, on_profile_update=None, summary=None, request_context=None):
        if request_context is not None:
            identity = request_context.identity
        if isinstance(identity, dict):
            identity = SimpleIdentity(
                erp_id=identity.get("erp_id"),
                role=identity.get("role"),
                dept=identity.get("dept"),
            )

        try:
            initial_state: AuraState = {
                "query": query,
                "history": history or [],
                "identity": identity,
                "request_context": request_context,
                "academic_scope": request_context.academic_scope if request_context else None,
                "display_profile": display_profile,
                "on_delta": on_delta,
                "on_profile_update": on_profile_update,
                "summary": summary or "",
                "result": None,
            }
            final_state = self._graph.invoke(initial_state)
            result = final_state.get("result")
            if result is None:
                # Should be unreachable — every path sets "result" before
                # END — but fail safe rather than return None to the API.
                log_soft_failure(
                    "AURA-GRAPH-001",
                    "graph.invoke",
                    detail="graph reached END without setting result",
                    visited=",".join(sorted(k for k in final_state if final_state.get(k) is not None)),
                )
                return {"answer": "Sorry, I encountered an error while generating a response. Please try again.", "sources": [], "is_personal_data": False}
            return result

        except Exception as e:
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["timeout", "timed out", "rate limit", "429", "connection"]):
                msg = "I'm experiencing a temporary connection issue. Please try again in a few seconds."
            else:
                msg = "Sorry, I encountered an error while generating a response. Please try again."
            log_soft_failure(
                "AURA-GRAPH-002",
                "graph.invoke",
                exc=e,
                user_facing="connection" if msg.startswith("I'm experiencing") else "soft_error",
            )
            return {"answer": msg, "sources": [], "is_personal_data": False}
