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
from pipeline.generation.answer_generator import AnswerGenerator
from pipeline.guardrails.query_guardrail import QueryGuardrail
from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
from pipeline.latency_tracker import track_segment

from erp_connector import ERPConnector
from erp_context_builder import ERPContextBuilder
from access_control import AccessControlGate, AccessDecision, resolve_effective_role
from audit_log import AuditLog
from personal_query_classifier import PersonalQueryClassifier

from pipeline.aura_chat import (
    GENERIC_DENIAL,
    PERSONAL_DATA_SYSTEM_ADDENDUM,
    is_greeting_or_meta,
)


class SimpleIdentity:
    def __init__(self, erp_id, role, dept=None):
        self.erp_id = erp_id
        self.role = role
        self.dept = dept


class AuraState(TypedDict, total=False):
    query: str
    history: list
    identity: Any
    display_profile: Any

    query_type: Optional[str]
    classification: dict
    user_role: str

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

        self._graph = self._build_graph()

    # ── Graph construction ──────────────────────────────────────────────

    def _build_graph(self):
        graph = StateGraph(AuraState)

        graph.add_node("safety_guardrail", self._n_safety_guardrail)
        graph.add_node("wellness_check", self._n_wellness_check)
        graph.add_node("greeting_check", self._n_greeting_check)
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
        graph.add_conditional_edges("greeting_check", route_or("classify"))
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
            is_safe = self.guardrail.is_safe(state["query"])
        if not is_safe:
            state["result"] = {
                "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
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

    def _n_classify(self, state: AuraState) -> AuraState:
        classification = self.classifier.classify(state["query"])
        state["classification"] = classification
        state["query_type"] = classification["type"]
        return state

    def _n_guest_gate(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        if query_type in ("PERSONAL", "MIXED", "AGGREGATE"):
            identity = state.get("identity")
            user_role = resolve_effective_role(identity) if identity else "guest"
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
            erp_data = {"aggregate": self.erp_connector.get_class_aggregate(course_code) if course_code else {}}
        else:
            erp_data = self._fetch_erp_data(classification["erp_fields"], target_erp_id, access_result)

        state["erp_context"] = self.context_builder.build(erp_data, identity, access_result)
        state["is_personal"] = True
        return state

    def _n_public_rag(self, state: AuraState) -> AuraState:
        query_type = state["query_type"]
        state.setdefault("rag_context", "")
        state.setdefault("sources", [])

        if query_type not in ("PUBLIC", "MIXED", "AGGREGATE"):
            return state

        identity = state.get("identity")
        user_role = resolve_effective_role(identity) if identity else "public"
        with track_segment("retrieval_time"):
            retrieval_result = self.pipeline.get_context(state["query"], state["history"], user_role=user_role)
        state["retrieval_result"] = retrieval_result
        state["chunks"] = retrieval_result.get("chunks", [])
        state["rag_context"] = retrieval_result.get("context", "")
        state["sources"] = retrieval_result.get("sources", [])

        if not state["chunks"] and query_type == "PUBLIC":
            state["result"] = {
                "answer": "I'm having trouble retrieving information right now. Please try again.",
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

        combined_context = "\n\n".join(filter(None, [erp_context, rag_context]))

        has_rag = query_type in ("PUBLIC", "MIXED") and bool(rag_context)

        with track_segment("generation_time"):
            answer = self.generator.generate(
                query=retrieval_result.get("corrected_query", state["query"]) if has_rag else state["query"],
                context=combined_context,
                plan=retrieval_result.get("plan") if has_rag else None,
                history=state["history"],
                profile=state.get("display_profile"),
                system_addendum=PERSONAL_DATA_SYSTEM_ADDENDUM if is_personal else None,
            )

        state["result"] = {
            "answer": answer,
            "sources": state.get("sources", []),
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

    def _fetch_erp_data(self, fields: list, roll_number: Optional[str], access_result) -> dict:
        if not roll_number:
            return {}
        data = {}
        course_scope = (access_result.course_codes[0] if access_result.course_codes else None)
        if "profile" in fields: data["profile"] = self.erp_connector.get_student_profile(roll_number)
        if "cgpa" in fields: data["cgpa"] = self.erp_connector.get_cgpa(roll_number)
        if "grades" in fields: data["grades"] = self.erp_connector.get_grades(roll_number, course_code=course_scope)
        if "attendance" in fields: data["attendance"] = self.erp_connector.get_attendance(roll_number, course_code=course_scope)
        if "advisees" in fields and getattr(access_result, "scope_type", None) in ("advisee", "all", "batch"):
            data["advisees"] = self.erp_connector.get_advisees(roll_number)
        if "courses" in fields: data["courses"] = self.erp_connector.get_faculty_courses(roll_number)
        return data

    # ── Public entrypoint (same signature/contract as AuraChat.chat) ────

    def chat(self, query, history=None, identity=None, display_profile=None):
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
                "display_profile": display_profile,
                "result": None,
            }
            final_state = self._graph.invoke(initial_state)
            result = final_state.get("result")
            if result is None:
                # Should be unreachable — every path sets "result" before
                # END — but fail safe rather than return None to the API.
                return {"answer": "Sorry, I encountered an error while generating a response. Please try again.", "sources": [], "is_personal_data": False}
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["timeout", "timed out", "rate limit", "429", "connection"]):
                msg = "I'm experiencing a temporary connection issue. Please try again in a few seconds."
            else:
                msg = "Sorry, I encountered an error while generating a response. Please try again."
            return {"answer": msg, "sources": [], "is_personal_data": False}
