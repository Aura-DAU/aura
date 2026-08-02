"""
AuraChat — reference implementation of the chat pipeline's 7-step flow.

NOTE: as of the LangGraph migration, `rag.py`'s AURA facade instantiates
`pipeline.aura_chat_graph.AuraChatGraph` (a LangGraph StateGraph), not
this class. This file is kept because AuraChatGraph imports its shared
constants/helpers (GENERIC_DENIAL, PERSONAL_DATA_SYSTEM_ADDENDUM,
is_greeting_or_meta) from here, and as a readable reference for the
control flow the graph reimplements node-by-node. The `AuraChat` class
below is otherwise unused.

The 7-step flow (from 06_query_routing.md) is now the primary path.
The existing RAG pipeline (Qdrant + BM25 + rerank) is called for
PUBLIC and the PUBLIC half of MIXED queries — it is completely unchanged.

Step 1: Classify (B9)
Step 2: Resolve target ERP ID
Step 3: Access control gate (B7)
Step 4: Audit log (B8)
Step 5: If DENIED → return denial message
Step 6: If PERSONAL/MIXED → fetch from ERP (B5), build context (B6)
Step 7: If PUBLIC/MIXED → run existing RAG pipeline
        Merge contexts → generate answer
"""

import re
from typing import Optional
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

from erp_connector import ERPConnector
from erp_context_builder import ERPContextBuilder
from access_control import AccessControlGate, AccessDecision
from audit_log import AuditLog
from personal_query_classifier import PersonalQueryClassifier

GENERIC_DENIAL = (
    "I'm not able to retrieve that information. "
    "If you believe you should have access to this data, "
    "please contact the Academic Office."
)

ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE = (
    "I don't have your academic programme details on file yet, so I can't "
    "retrieve curriculum-specific information accurately. Please sign out and "
    "sign back in once, then try your question again."
)

RETRIEVAL_FAILURE_RESPONSE = (
    "I'm having trouble retrieving information right now. Please try again."
)

PERSONAL_DATA_SYSTEM_ADDENDUM = """
------------------------------------------------------------
PERSONAL DATA IN CONTEXT
------------------------------------------------------------
When the context contains a <personal_data> block, this is live,
real-time data from DAU's ERP system for the logged-in user.

- Always present personal data as current fact, not a retrieved excerpt.
  Say "Your current CGPA is 8.34" not "According to the retrieved document..."
- Never quote sources for personal data — there is no URL to link to.
- Never speculate about what the personal data means beyond what is stated.
  "Your attendance in IT205 is 68.2%" is correct.
  "You may fail IT205 due to attendance" is speculation — do not add this.
- If the <personal_data> block is present but a field the user asked about
  is missing from it, say clearly that this specific data is not available
  in your current access rather than guessing.
"""


def is_greeting_or_meta(query):
    q = re.sub(r'[?.!,]+$', '', query.strip()).lower().strip()
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning",
        "good afternoon", "good evening", "how are you", "who are you",
        "who is aura", "what is aura", "what can you do", "help", "menu",
        "intro", "introduce yourself", "thank you", "thanks", "bye",
        "goodbye", "see you", "good night", "have a nice day", "have a good day",
        "cya", "cheers", "thanks aura"
    }
    if q in greetings:
        return True
    words = q.split()
    if len(words) <= 4 and any(w in greetings for w in words):
        return True
    return False


class SimpleIdentity:
    def __init__(self, d):
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


class AuraChat:

    def __init__(self):
        self.pipeline   = RetrievalPipeline()
        self.generator  = AnswerGenerator()
        self.guardrail  = QueryGuardrail()
        self.wellness   = WellnessGuardrail()

        erp = ERPConnector()
        self.classifier     = PersonalQueryClassifier()
        self.erp_connector  = erp
        self.context_builder = ERPContextBuilder()
        self.access_gate    = AccessControlGate(erp)
        self.audit_log      = AuditLog()

    def chat(self, query, history=None, identity=None, display_profile=None):
        # Convert dict identity to a simple object with dot-attribute access to avoid AttributeError
        if isinstance(identity, dict):
            identity = SimpleIdentity(identity)

        try:
            # ── Middleware 1: Institution Context Resolver & Privacy Gate ──
            from access_control import resolve_effective_role
            from institution_resolver import get_institution_resolver
            from privacy_filter import ResponsePrivacyFilter

            user_role = resolve_effective_role(identity) if identity else "public"
            privacy_filter = ResponsePrivacyFilter(user_role=user_role)

            # Check explicit privacy policy violation requests (e.g. mobile numbers, student IDs for unauthorized roles)
            is_blocked, refusal_msg = privacy_filter.check_explicit_privacy_request(query)
            if is_blocked:
                return {
                    "answer": refusal_msg,
                    "sources": [],
                    "is_personal_data": False,
                }

            # Resolve institutional abbreviations (DADC -> Dance Club (DADC) at DAU)
            query = get_institution_resolver().resolve(query)

            from pipeline.latency_tracker import track_segment
            history = history or []

            # ── 1. Greetings & Meta Fast-Path ─────────────────────────
            if is_greeting_or_meta(query):
                q = re.sub(r'[?.!,]+$', '', query.strip()).lower().strip()
                words = q.split()
                help_words = {"what can you do", "help", "menu", "intro", "introduce yourself"}
                who_words = {"who are you", "who is aura", "what is aura"}
                
                if q in help_words or any(w in help_words for w in words):
                    ans = (
                        "I can help you with a wide range of questions about Dhirubhai Ambani University, including:\n"
                        "- **Admissions & Academics**: Program details, fee structures, eligibility criteria, and academic policies.\n"
                        "- **Campus & Facilities**: Hostel rules, dining details, medical SOPs, and general guidelines.\n"
                        "- **Calendar Actions**: I can help you schedule appointments or check event dates.\n\n"
                        "How can I assist you today?"
                    )
                elif q in who_words or any(w in who_words for w in words):
                    ans = (
                        "I am AURA, the official AI assistant for Dhirubhai Ambani University (DAU). "
                        "I am here to help you navigate university life, policies, academics, and admissions. "
                        "How can I help you today?"
                    )
                else:
                    ans = (
                        "Hello! I am AURA, the official AI assistant for Dhirubhai Ambani University (DAU). "
                        "I can help you with questions about admissions, academics, faculty, courses, and campus life. "
                        "How can I assist you today?"
                    )
                return {"answer": ans, "sources": [], "is_personal_data": False}

            # ── 2. Pure Profile Questions Fast-Path (<1ms, Bypasses RAG & Wellness) ──
            from personal_query_classifier import is_pure_profile_query
            if is_pure_profile_query(query) and identity:
                name = getattr(identity, "full_name", None) or "Student"
                roll = getattr(identity, "roll_number", None) or getattr(identity, "erp_id", "N/A")
                prog = getattr(identity, "program", None) or "B.Tech. (ICT)"
                branch = getattr(identity, "branch", None) or getattr(identity, "dept", "ICT")
                sem = getattr(identity, "current_sem", None) or 5
                email = getattr(identity, "email", None) or f"{roll.lower()}@dau.ac.in"

                q_lower = query.lower()
                if "name" in q_lower or "who am i" in q_lower:
                    ans = f"You are **{name}** (Roll Number: `{roll}`)."
                elif "roll" in q_lower or "id" in q_lower:
                    ans = f"Your roll number is `{roll}`."
                elif "email" in q_lower:
                    ans = f"Your official university email is `{email}`."
                elif "branch" in q_lower or "dept" in q_lower:
                    ans = f"You are in the **{branch}** department."
                elif "semester" in q_lower:
                    ans = f"You are currently in **Semester {sem}** of the {prog} program."
                else:
                    ans = (
                        f"You are **{name}** (Roll Number: `{roll}`), currently enrolled in "
                        f"**Semester {sem}** of the **{prog}** program in the **{branch}** department."
                    )
                return {"answer": ans, "sources": [], "is_personal_data": True}

            # ── 3. Wellness / Distress Check ────────────────────────────
            if self.wellness.check(query):
                return {
                    "answer": self.wellness.get_response(),
                    "sources": [],
                    "is_personal_data": False,
                }

            # ── 4. Safety + Scope Guardrail ────────────────────────────
            with track_segment("guardrail_time"):
                verdict = self.guardrail.classify(query)
            if verdict is Verdict.UNSAFE:
                return {
                    "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                    "sources": [],
                }
            if verdict is Verdict.OFF_TOPIC:
                return {
                    "answer": OFF_TOPIC_RESPONSE,
                    "sources": [],
                }

            # ── 5. Intent Classification ────────────────────────────────
            classification = self.classifier.classify(query, history=history)
            query_type     = classification["type"]   # PUBLIC | PERSONAL | MIXED

            # ── Guest / No-identity check for personal paths ───────────
            if query_type in ("PERSONAL", "MIXED", "AGGREGATE"):
                from access_control import resolve_effective_role
                user_role = resolve_effective_role(identity) if identity else "guest"
                if user_role == "guest":
                    return {
                        "answer": GENERIC_DENIAL,
                        "sources": [],
                        "is_personal_data": False,
                    }

            # ── Step 1b: Strict guardrail for personal-data paths ───────
            # is_safe() above fails OPEN (acceptable for public RAG). For
            # personal/ERP paths we re-check with is_safe_strict() which
            # fails CLOSED — if the guardrail LLM is down, deny rather than
            # risk a prompt injection reaching the ERP pipeline.
            if query_type in ("PERSONAL", "MIXED", "AGGREGATE") and identity:
                with track_segment("guardrail_time"):
                    is_safe_strict = self.guardrail.is_safe_strict(query)
                if not is_safe_strict:
                    return {
                        "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                        "sources": [],
                        "is_personal_data": False,
                    }

            erp_context   = ""
            is_personal   = False

            # ── Steps 2–6: Personal and Aggregate data paths ──────────
            if query_type in ("PERSONAL", "MIXED", "AGGREGATE") and identity:
                target_erp_id = self._resolve_target(classification["target"], identity)

                # Step 3: Access control gate
                access_result = self.access_gate.evaluate(
                    identity=identity,
                    query_intent=classification,
                    target_identifier=target_erp_id,
                )

                # Step 4: Audit log (always — both ALLOWED and DENIED)
                self.audit_log.record(
                    erp_id=identity.erp_id,
                    role=identity.role,
                    query_text=query,
                    query_type=query_type.lower(),
                    target_erp_id=target_erp_id,
                    access_granted=(access_result.decision == AccessDecision.ALLOWED),
                    denial_reason=access_result.reason if access_result.decision == AccessDecision.DENIED else None,
                    erp_tables=classification.get("erp_fields", []),
                    scope_context=getattr(access_result, "scope_context", None),
                )

                # Step 5: If DENIED → return generic message
                if access_result.decision == AccessDecision.DENIED:
                    return {"answer": GENERIC_DENIAL, "sources": [], "is_personal_data": False}

                # Step 6: Fetch from ERP and build context
                if query_type == "AGGREGATE":
                    course_code = (access_result.course_codes[0] if access_result.course_codes else None)
                    erp_data = {"aggregate": self.erp_connector.get_class_aggregate(course_code) if course_code else {}}
                else:
                    erp_data = self._fetch_erp_data(
                        classification["erp_fields"],
                        target_erp_id,
                        access_result,
                        requester_erp_id=identity.erp_id,
                        identity=identity,
                    )
                erp_context = self.context_builder.build(erp_data, identity, access_result)
                is_personal = True

            # ── Step 7: Public RAG (for PUBLIC and MIXED) ──────────────
            rag_context = ""
            sources     = []
            if query_type in ("PUBLIC", "MIXED", "AGGREGATE"):
                from access_control import resolve_effective_role
                user_role = resolve_effective_role(identity) if identity else "public"
                with track_segment("retrieval_time"):
                    retrieval_result = self.pipeline.get_context(query, history, user_role=user_role)
                chunks    = retrieval_result.get("chunks", [])
                rag_context = retrieval_result.get("context", "")
                sources   = retrieval_result.get("sources", [])

                if not chunks and query_type == "PUBLIC":
                    reason = retrieval_result.get("abstention_reason")
                    answer = (
                        ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE
                        if reason == "academic_scope_unavailable"
                        else RETRIEVAL_FAILURE_RESPONSE
                    )
                    return {"answer": answer, "sources": [], "is_personal_data": False}

            # ── Step 8: Merge, Sanitize Context, and Generate ─────────
            combined_context = "\n\n".join(filter(None, [erp_context, rag_context]))
            combined_context = privacy_filter.sanitize_retrieved_context(combined_context)

            with track_segment("generation_time"):
                answer = self.generator.generate(
                    query=retrieval_result.get("corrected_query", query) if query_type in ("PUBLIC", "MIXED") and rag_context else query,
                    context=combined_context,
                    plan=retrieval_result.get("plan") if query_type in ("PUBLIC", "MIXED") and rag_context else None,
                    history=history,
                    profile=display_profile,
                    system_addendum=PERSONAL_DATA_SYSTEM_ADDENDUM if is_personal else None,
                    tracking_flags=request_context.tracking_flags if request_context else None,
                )

            # Apply Post-generation Privacy Filter (scans and redacts leaked PII / restricted fields)
            answer = privacy_filter.filter_response_text(answer, query=query)

            return {
                "answer": answer,
                # public sources only — never ERP data — and narrowed to the
                # docs the answer actually cited
                "sources": filter_sources_by_citations(
                    sources,
                    retrieval_result.get("citation_map", {}),
                    answer,
                ),
                "is_personal_data": is_personal,
            }

        except Exception as e:
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["timeout", "timed out", "rate limit", "429", "connection"]):
                msg = "I'm experiencing a temporary connection issue. Please try again in a few seconds."
            else:
                msg = "Sorry, I encountered an error while generating a response. Please try again."
            log_soft_failure(
                "AURA-CHAT-001",
                "aura_chat.chat",
                exc=e,
                user_facing="connection" if msg.startswith("I'm experiencing") else "soft_error",
            )
            return {"answer": msg, "sources": [], "is_personal_data": False}

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
        identity=None,
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
        # Timetable is in AURA's own PostgreSQL — never goes through RAG/Qdrant.
        if "timetable" in fields and identity is not None:
            try:
                from pipeline.timetable.service import get_effective_timetable
                data["timetable"] = get_effective_timetable(identity)
            except Exception as _tt_err:
                import logging
                logging.getLogger(__name__).warning(
                    "Timetable fetch skipped in _fetch_erp_data: %s", _tt_err
                )
        return data

    def _rag_only(self, query, history, profile, user_role: str = "public") -> dict:
        from pipeline.latency_tracker import track_segment
        with track_segment("retrieval_time"):
            retrieval_result = self.pipeline.get_context(query, history, user_role=user_role)
        chunks    = retrieval_result.get("chunks", [])
        if not chunks:
            return {"answer": "I'm having trouble retrieving information. Please try again.", "sources": [], "is_personal_data": False}
        with track_segment("generation_time"):
            answer = self.generator.generate(
                query=retrieval_result.get("corrected_query", query),
                context=retrieval_result["context"],
                plan=retrieval_result["plan"],
                history=history,
                profile=profile,
            )
        return {
            "answer": answer,
            "sources": filter_sources_by_citations(
                retrieval_result["sources"],
                retrieval_result.get("citation_map", {}),
                answer,
            ),
            "is_personal_data": False,
        }
