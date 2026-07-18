# AuraChat — main chat pipeline.
# The 7-step flow (from 06_query_routing.md) is now the primary path.
# Merge contexts → generate answer

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
from pipeline.generation.answer_generator import AnswerGenerator
from pipeline.guardrails.query_guardrail import QueryGuardrail
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
        "intro", "introduce yourself"
    }
    if q in greetings:
        return True
    words = q.split()
    if len(words) <= 3 and any(w in greetings for w in words):
        return True
    return False


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

    def chat(self, query, history=None, identity=None, display_profile=None, on_delta=None):
        # on_delta: optional callable(str) receiving sanitised answer deltas as
        # they stream from the LLM. Canned paths (guardrail denials, greetings,
        # wellness, access denials) never invoke it — callers detect "nothing
        # streamed" and fall back to emitting the returned answer whole.
        # Convert dict identity to a simple object with dot-attribute access to avoid AttributeError
        if isinstance(identity, dict):
            class SimpleIdentity:
                def __init__(self, erp_id, role, dept=None):
                    self.erp_id = erp_id
                    self.role = role
                    self.dept = dept
            identity = SimpleIdentity(
                erp_id=identity.get("erp_id"),
                role=identity.get("role"),
                dept=identity.get("dept")
            )

        try:
            from pipeline.latency_tracker import track_segment

            history = history or []
            is_greeting = is_greeting_or_meta(query)

            # ── Pre-flight checks (parallelised) ───────────────────────
            # The safety guardrail, wellness/distress check and personal-query
            # classifier are independent LLM round-trips over the raw query;
            # running them sequentially added two full RTTs to every request.
            # Wellness + classifier run on worker threads while the guardrail
            # runs here; results are consumed in the original precedence order
            # (guardrail → wellness → greeting → classification) so routing
            # behaviour is unchanged.
            with ThreadPoolExecutor(max_workers=2) as preflight:
                wellness_future = preflight.submit(self.wellness.check, query)
                # Greetings never reach the classifier — don't spend the call.
                classify_future = (
                    None if is_greeting
                    else preflight.submit(self.classifier.classify, query)
                )

                # ── Safety guardrail (applies to every query) ──────────
                # Fails OPEN (None verdict → allow), exactly like the old
                # is_safe() call; personal paths re-check below.
                with track_segment("guardrail_time"):
                    guardrail_verdict = self.guardrail.evaluate(query)
                if guardrail_verdict is False:
                    return {
                        "answer": "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
                        "sources": [],
                    }

                # ── Wellness/distress check ───────────────────────────
                if wellness_future.result():
                    return {
                        "answer": self.wellness.get_response(),
                        "sources": [],
                        "is_personal_data": False,
                    }

            # ── Greetings bypass classifier ────────────────────────────
            if is_greeting:
                q = re.sub(r'[?.!,]+$', '', query.strip()).lower().strip()
                words = q.split()
                
                # Check for help/capabilities queries
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
                return {
                    "answer": ans,
                    "sources": [],
                    "is_personal_data": False
                }

            # ── Step 1: Classify (already running since pre-flight) ─────
            # classify_future is always set here — greeting queries returned above.
            assert classify_future is not None
            classification = classify_future.result()
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
            # The pre-flight guardrail fails OPEN (acceptable for public RAG);
            # personal/ERP paths must fail CLOSED. When the pre-flight call
            # produced a real verdict it is reused — it's the same
            # deterministic temperature-0 classification, so re-asking only
            # adds a full LLM round-trip, not safety. Only when the pre-flight
            # call errored (verdict None, allowed through by fail-open) do we
            # re-attempt via is_safe_strict(), which denies if the guardrail
            # LLM is still down — no prompt injection reaches the ERP pipeline
            # unchecked.
            if (
                query_type in ("PERSONAL", "MIXED", "AGGREGATE")
                and identity
                and guardrail_verdict is None
            ):
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
                    erp_data = self._fetch_erp_data(classification["erp_fields"], target_erp_id, access_result)
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
                    return {"answer": "I'm having trouble retrieving information right now. Please try again.", "sources": [], "is_personal_data": False}

            # ── Step 8: Merge and generate ─────────────────────────────
            combined_context = "\n\n".join(filter(None, [erp_context, rag_context]))

            with track_segment("generation_time"):
                answer = self.generator.generate(
                    query=retrieval_result.get("corrected_query", query) if query_type in ("PUBLIC", "MIXED") and rag_context else query,
                    context=combined_context,
                    plan=retrieval_result.get("plan") if query_type in ("PUBLIC", "MIXED") and rag_context else None,
                    history=history,
                    profile=display_profile,
                    system_addendum=PERSONAL_DATA_SYSTEM_ADDENDUM if is_personal else None,
                    on_delta=on_delta,
                )

            return {
                "answer": answer,
                "sources": sources,          # public sources only — never ERP data
                "is_personal_data": is_personal,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["timeout", "timed out", "rate limit", "429", "connection"]):
                msg = "I'm experiencing a temporary connection issue. Please try again in a few seconds."
            else:
                msg = "Sorry, I encountered an error while generating a response. Please try again."
            return {"answer": msg, "sources": [], "is_personal_data": False}

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
        if "profile"    in fields: data["profile"]    = self.erp_connector.get_student_profile(roll_number)
        if "cgpa"       in fields: data["cgpa"]        = self.erp_connector.get_cgpa(roll_number)
        if "grades"     in fields: data["grades"]      = self.erp_connector.get_grades(roll_number, course_code=course_scope)
        if "attendance" in fields: data["attendance"]  = self.erp_connector.get_attendance(roll_number, course_code=course_scope)
        if "advisees"   in fields and getattr(access_result, "scope_type", None) in ("advisee", "all", "batch"):
            data["advisees"] = self.erp_connector.get_advisees(roll_number)
        if "courses"    in fields: data["courses"]     = self.erp_connector.get_faculty_courses(roll_number)
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
        return {"answer": answer, "sources": retrieval_result["sources"], "is_personal_data": False}