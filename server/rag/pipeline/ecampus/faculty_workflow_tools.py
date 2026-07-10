"""
Faculty workflow guidance tools — leave application, CPDA/conference travel
approval, and seed grant application guidance.

These are deliberately CHAT-BASED GUIDANCE ONLY: none of them submit an
application, write to eCampus, or contact HR/Dean R&D on the faculty
member's behalf. Each one retrieves the relevant policy text from the RAG
knowledge base (so figures like grant amounts/thresholds stay sourced from
the indexed policy doc rather than hardcoded and going stale) and returns a
structured checklist the LLM can present conversationally.

# TODO(unirp): Replace with UniRP endpoint — routes TBD. Do NOT implement any
# UniRP logic. If/when leave, CPDA, or seed grant applications move to a
# UniRP-backed transactional API, these handlers should call that instead of
# only returning guidance — but do not build that integration until routes
# are confirmed.
"""

from ..personal_data.access_control import AccessDenied
from ..personal_data.audit import audit_log


def _retrieve_policy_context(query: str) -> str:
    """Same pattern as composite_tools._attendance_threshold — pull the
    authoritative text out of the indexed KB rather than hardcoding figures
    that can change between policy revisions. Falls back to a plain notice
    if retrieval isn't available, rather than silently fabricating policy."""
    try:
        from ..retrieval.retrieval_pipeline import RetrievalPipeline
        result = RetrievalPipeline().get_context(query)
        context = (result or {}).get("context", "")
        return context or "No matching policy text was retrieved — verify with HR / Dean (R&D) directly."
    except Exception as e:
        return f"Policy retrieval unavailable ({e}) — verify with HR / Dean (R&D) directly."


def _require_faculty(identity: dict, tool_name: str) -> None:
    if not identity or identity.get("role") != "faculty":
        raise AccessDenied(f"Only faculty may use the {tool_name} tool.")


# ── Faculty leave application initiation ────────────────────────────────
def handle_faculty_leave_application(identity: dict, **kwargs) -> dict:
    _require_faculty(identity, "faculty leave application")

    leave_type = (kwargs.get("leave_type") or "").strip()
    duration_days = kwargs.get("duration_days")

    context = _retrieve_policy_context(
        "faculty staff leave policy application process approval "
        "casual earned medical maternity paternity academic study leave"
    )

    normalized = leave_type.lower()
    if normalized in {"casual", "casual leave", "cl"}:
        approval_chain = [
            "Casual Leave needs no formal application — simply inform your HOD.",
        ]
    elif isinstance(duration_days, (int, float)) and duration_days >= 10:
        approval_chain = [
            "Submit the designated Leave Google Form.",
            "Routed to the Dean (Faculty) for approval — required for leave of 10 or more days.",
        ]
    else:
        approval_chain = [
            "Submit the designated Leave Google Form.",
            "Routed to your HOD for approval — applies to leave under 10 days (other than Casual Leave).",
        ]

    audit_log(identity, query="faculty_leave_application", allowed=True, target=identity.get("erp_id"))

    return {
        "leave_type_requested": leave_type or "not specified",
        "duration_days": duration_days,
        "approval_chain": approval_chain,
        "checklist": [
            "Confirm the leave type against the entitlement table (Casual / Earned / Medical / Maternity / Paternity / Academic-Study / CPDA).",
            "Medical Leave requires a medical certificate.",
            "Academic/Study Leave requires advance planning and Director approval.",
            "Casual Leave cannot be combined with any other leave category; combined with weekends/holidays it must not exceed 7 days at a stretch.",
            "Return any borrowed library material before proceeding on long leave or deputation.",
        ],
        "policy_context": context,
        "note": (
            "This tool only provides guidance — it does not submit any application or notify HR/HOD/Dean. "
            "Confirm current entitlements and the leave form link with the HR/Administration office."
        ),
    }


# ── CPDA / conference travel approval guidance ───────────────────────────
def handle_cpda_travel_approval(identity: dict, **kwargs) -> dict:
    _require_faculty(identity, "CPDA travel approval")

    conference_type = (kwargs.get("conference_type") or "").strip()
    requested_amount_inr = kwargs.get("requested_amount_inr")

    context = _retrieve_policy_context(
        "CPDA cumulative professional development allowance conference travel "
        "policy application procedure approval Dean R&D"
    )

    if isinstance(requested_amount_inr, (int, float)):
        if requested_amount_inr > 100000:
            approval_note = (
                "Requested amount exceeds Rs. 1 lakh — Dean (R&D) must obtain the Director's "
                "approval before sanctioning."
            )
        else:
            approval_note = "Requested amount is at or under Rs. 1 lakh — Dean (R&D) may approve it directly."
    else:
        approval_note = (
            "Dean (R&D) approves directly for requests up to Rs. 1 lakh; anything above that needs "
            "the Director's approval as well."
        )

    audit_log(identity, query="cpda_travel_approval", allowed=True, target=identity.get("erp_id"))

    return {
        "conference_type": conference_type or "not specified",
        "requested_amount_inr": requested_amount_inr,
        "eligibility_checklist": [
            "Faculty member must be past confirmation of service to hold a CPDA balance.",
            "CPDA funds cannot be used while on lien or extraordinary leave.",
            "Available balance is the sum of up to 3 years of grants (current year + prior 2), each Rs. 1 lakh/year — confirm your current balance before applying.",
        ],
        "required_documents": [
            "Conference dates and location",
            "Conference rank (A*, A, B, or DAU-approved/other)",
            "Acceptance notification and acceptance rate (if applicable)",
            "Title, abstract, and author list of the paper",
            "Manuscript draft of the accepted paper",
            "Requested CPDA amount broken down into registration, travel, and accommodation",
        ],
        "approval_steps": [
            "Email the application with all required documents to the Dean of R&D.",
            approval_note,
            "The decision is communicated back to the applicant by the Dean (R&D) via email.",
        ],
        "policy_context": context,
        "note": (
            "This tool only produces guidance — it does not email or submit anything on the faculty "
            "member's behalf. Verify the current CPDA balance and limits against the official CPDA Policy."
        ),
    }


# ── Seed grant application guidance ──────────────────────────────────────
def handle_seed_grant_guidance(identity: dict, **kwargs) -> dict:
    _require_faculty(identity, "seed grant guidance")

    proposed_budget_inr = kwargs.get("proposed_budget_inr")

    context = _retrieve_policy_context(
        "seed grant policy newly recruited faculty proposal category application review process"
    )

    category = None
    over_ceiling = False
    if isinstance(proposed_budget_inr, (int, float)):
        if proposed_budget_inr <= 200000:
            category = "A"
        elif proposed_budget_inr <= 500000:
            category = "B"
        elif proposed_budget_inr <= 1000000:
            category = "C"
        else:
            over_ceiling = True

    audit_log(identity, query="seed_grant_guidance", allowed=True, target=identity.get("erp_id"))

    return {
        "proposed_budget_inr": proposed_budget_inr,
        "suggested_category": category,
        "over_ceiling": over_ceiling,
        "eligibility_checklist": [
            "Open only to newly recruited faculty early in their career — Ph.D. awarded within the last three years.",
            "Only one seed grant application is allowed, within a year of joining the university.",
            "Project duration is capped at two years.",
        ],
        "proposal_structure": [
            "Name of the Investigator",
            "Title of the Seed Grant Research Proposal",
            "Name of the Area/Department",
            "Background of the Research (context and importance; gaps in existing knowledge/technology)",
            "Research Objective, Methodology, Timeline",
            "Budget Estimate and Justification (year-wise)",
            "Expected Outcomes and Impact",
            "(Category B/C only) Names of three external experts in the field of the proposal",
        ],
        "review_process": {
            "A": "Reviewed by one internal subject-matter expert identified by the Dean (R&D).",
            "B": "Reviewed by two experts (internal or external); approved proposals get a Research "
                 "Progress Committee reviewing progress every six months.",
            "C": "Reviewed by three experts (at least two external); approved proposals get a Research "
                 "Progress Committee reviewing progress every six months.",
        },
        "reporting_obligations": (
            "Category B/C projects are reviewed every six months by the Research Progress Committee. "
            "Category A cannot cover technical-staff costs; Category B/C can, up to 50% of the "
            "sanctioned fund."
        ),
        "deadline_reminder": (
            "The seed grant can only be requested once, within a year of joining — apply early, since "
            "eligibility is tied to how recently the Ph.D. was awarded (within 3 years) and time since "
            "joining, not to a fixed calendar deadline."
        ),
        "policy_context": context,
        "note": (
            "This tool only provides guidance — it does not submit a proposal to the Dean (R&D). "
            "Confirm current budget ceilings and review composition against the official Seed Grant Policy."
        ),
    }
