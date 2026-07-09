"""
Composite tools — handlers that combine more than one raw eCampus call (or
an eCampus call + the RAG knowledge base) into one higher-value answer, so
the LLM doesn't have to chain several tool calls itself for common
questions. Registered in tool_registry.py alongside the single-source tools.
"""

import os
from . import cache
from .client import ECampusClient
from .credentials_vault import (
    CredentialsNotLinked,
    has_advisor_consent,
    grant_advisor_consent,
    revoke_advisor_consent,
    list_consented_faculty,
)
from ..personal_data.access_control import authorize_personal_query, AccessDenied
from ..personal_data.audit import audit_log

DEFAULT_ATTENDANCE_THRESHOLD = 75.0  # fallback only — prefer the RAG-sourced value below


def _own_client(identity) -> ECampusClient:
    """Raises AccessDenied (identity) or CredentialsNotLinked (vault) —
    callers must handle both."""
    student_id = authorize_personal_query(identity, target_student_id=None)
    return ECampusClient(erp_id=student_id)


def _attendance_threshold() -> float:
    """Pulls the real attendance-eligibility threshold from the indexed
    Academic Handbook rather than hardcoding it, since policy doc text is
    the authoritative source and can change between catalog years."""
    try:
        from ..retrieval.retrieval_pipeline import RetrievalPipeline
        import re
        result = RetrievalPipeline().get_context("minimum attendance percentage examination eligibility")
        match = re.search(r"(\d{2})\s*%", result.get("context", ""))
        if match:
            return float(match.group(1))
    except Exception:
        # Fallback to default threshold if handbook retrieval fails
        pass
    return DEFAULT_ATTENDANCE_THRESHOLD


# ── check_exam_eligibility ──────────────────────────────────────────────
def check_exam_eligibility(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
        attendance = client.get_attendance()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}

    threshold = _attendance_threshold()
    at_risk = []
    for course in attendance:
        try:
            pct = float(str(course.get("percentage", "0")).replace("%", ""))
        except ValueError:
            continue
        if pct < threshold:
            at_risk.append({**course, "threshold": threshold})

    audit_log(identity, query="check_exam_eligibility", allowed=True, target=client.erp_id)
    return {
        "threshold_used": threshold,
        "at_risk_courses": at_risk,
        "eligible_for_all_exams": len(at_risk) == 0,
        "note": "Threshold sourced from the Academic Handbook where available; verify against the official policy for edge cases (medical exemptions, etc.) rather than treating this as final.",
    }


# ── get_academic_snapshot ───────────────────────────────────────────────
def get_academic_snapshot(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    snapshot = {}
    errors = {}
    for key, fn in [
        ("cgpa", client.get_cgpa),
        ("attendance", client.get_attendance),
        ("fees", client.get_fees),
        ("hostel", client.get_hostel),
        ("registration", client.get_registration),
    ]:
        try:
            snapshot[key] = fn()
        except Exception as e:
            errors[key] = str(e)

    audit_log(identity, query="get_academic_snapshot", allowed=True, target=client.erp_id)
    if errors:
        snapshot["_partial_errors"] = errors
    return snapshot


# ── compare_semester_trend ──────────────────────────────────────────────
def compare_semester_trend(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
        result = client.get_result()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}

    by_semester: dict[str, list] = {}
    for g in result.get("grades", []):
        by_semester.setdefault(g.get("semester", "unknown"), []).append(g)

    audit_log(identity, query="compare_semester_trend", allowed=True, target=client.erp_id)
    return {
        "semesters_seen": sorted(by_semester.keys()),
        "courses_per_semester": {sem: len(courses) for sem, courses in by_semester.items()},
        "note": "SGPA-level numeric trend requires parsers.parse_result's TODOs to be filled in with real per-semester SGPA values — this returns the grade breakdown available today.",
    }


# ── refresh_my_data ──────────────────────────────────────────────────────
def refresh_my_data(identity, **kwargs) -> dict:
    student_id = authorize_personal_query(identity, target_student_id=None)
    cache.invalidate(student_id)
    audit_log(identity, query="refresh_my_data", allowed=True, target=student_id)
    return {"status": "cache cleared — next request will re-fetch from eCampus"}


# ── share_data_with_advisor / revoke_advisor_access ───────────────────────
def share_data_with_advisor(identity, faculty_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can grant advisor data-sharing consent.")
    grant_advisor_consent(identity["erp_id"], faculty_erp_id)
    audit_log(identity, query="share_data_with_advisor", allowed=True, target=faculty_erp_id)
    return {"status": "shared", "faculty_erp_id": faculty_erp_id}


def revoke_advisor_access(identity, faculty_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can revoke advisor data-sharing consent.")
    revoke_advisor_consent(identity["erp_id"], faculty_erp_id)
    audit_log(identity, query="revoke_advisor_access", allowed=True, target=faculty_erp_id)
    return {"status": "revoked", "faculty_erp_id": faculty_erp_id}


def list_my_data_sharing(identity, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can view their own data-sharing settings.")
    return {"shared_with": list_consented_faculty(identity["erp_id"])}


# ── get_advisee_snapshot (faculty, consent-gated) ──────────────────────
def get_advisee_snapshot(identity, student_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "faculty":
        raise AccessDenied("Only faculty may request an advisee's academic snapshot.")

    # Consent check FIRST, before the generic role-based check — a faculty
    # member being a real advisor in eCampus is not sufficient on its own
    # under the credential-vault model (see access_control.py's note).
    if not has_advisor_consent(student_erp_id, identity["erp_id"]):
        audit_log(identity, query="get_advisee_snapshot", allowed=False, target=student_erp_id,
                   reason="Student has not shared data with this faculty member.")
        return {
            "error": "This student hasn't shared their academic data with you through AURA.",
            "action_needed": "student_consent_required",
        }

    target_id = authorize_personal_query(identity, target_student_id=student_erp_id)
    client = ECampusClient(erp_id=target_id)
    try:
        snapshot = {
            "cgpa": client.get_cgpa(),
            "attendance": client.get_attendance(),
        }
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "student_has_not_linked_ecampus"}

    audit_log(identity, query="get_advisee_snapshot", allowed=True, target=target_id)
    return snapshot


_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client

def get_document_request_guidance(identity, document_type: str, **kwargs) -> dict:
    """
    Retrieves the procedure for requesting a specific document from the Knowledge Base (KB)
    and uses a structured LLM call to return a checklist, handling office, and processing time.
    """
    from ..retrieval.retrieval_pipeline import RetrievalPipeline
    import json
    
    # 1. Map document type to a semantically rich query
    query_mapping = {
        "bonafide": "bonafide certificate request procedure application online fee time office",
        "transcript": "transcript certificate request procedure academic records online fee time office",
        "id_card": "student smart id card replacement procedure card loss application fee office",
        "fee_structure": "fee structure details cost of program tuition hostel charges",
        "grade_report": "combine grade report semester-wise mark sheet request procedure",
        "other": "requesting academic documents student document service process"
    }
    
    search_query = query_mapping.get(document_type.lower(), "requesting academic documents student document service process")
    
    # 2. Query the Knowledge Base (RAG)
    try:
        retrieval_res = RetrievalPipeline().get_context(search_query)
        context = retrieval_res.get("context", "")
    except Exception as e:
        context = ""
        
    if not context.strip():
        # Fallback if KB retrieval is completely empty
        return {
            "checklist": ["Submit a formal request through the online document portal."],
            "handling_office": "Registrar's Office / CoE Office (documents@daiict.ac.in)",
            "processing_time": "Usually 2-3 working days",
            "required_documents_and_fees": "Refer to the online document portal for specific charges."
        }

    # 3. Use LLM to extract structured fields from the retrieved KB context
    system_prompt = """
You are an information extraction assistant for Dhirubhai Ambani University.
Your task is to read the retrieved university guidelines context and extract details about how a student can request a specific document type.

Extract the following fields from the context:
1. checklist: A list of step-by-step actions/guidelines the student must follow. Keep each step clear and concise.
2. handling_office: The office or email/phone contact responsible for this document request (e.g. CoE Office, Registrar's Office, documents@daiict.ac.in, emergency phone).
3. processing_time: How long it typically takes to process and issue the document (e.g., 2 working days).
4. required_documents_and_fees: Any fees or required attachments/verification documents mentioned (e.g. specific charges, ID proofs).

Output ONLY valid JSON matching this format (no markdown code blocks, no additional text):
{
  "checklist": ["step 1", "step 2"],
  "handling_office": "Office details...",
  "processing_time": "Processing time...",
  "required_documents_and_fees": "Fees and document details..."
}
"""

    user_content = f"Document Type: {document_type}\n\nRetrieved Guidelines Context:\n{context}"

    try:
        client = _get_groq_client()
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_content}
            ]
        )
        
        raw_content = response.choices[0].message.content.strip()
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(raw_content)
        
        if not isinstance(parsed.get("checklist"), list):
            parsed["checklist"] = [str(parsed.get("checklist", "Follow standard procedure."))]
            
        parsed.setdefault("handling_office", "Registrar's Office / CoE Office")
        parsed.setdefault("processing_time", "2 working days")
        parsed.setdefault("required_documents_and_fees", "Refer to the online portal.")
        
        audit_log(identity, query=f"get_document_request_guidance:{document_type}", allowed=True, target="kb")
        return parsed
        
    except Exception as e:
        audit_log(identity, query=f"get_document_request_guidance:{document_type}", allowed=False, target="kb", reason=str(e))
        return {
            "checklist": ["Submit request through the online portal."],
            "handling_office": "Registrar's Office (documents@daiict.ac.in)",
            "processing_time": "Usually 2 working days",
            "required_documents_and_fees": "Refer to the online document portal for specific charges."
        }


def get_hostel_complaint_guidance(identity, complaint_type: str, **kwargs) -> dict:
    """
    Retrieves the procedure, contact persons, and steps for filing a hostel-related complaint from the KB,
    and returns a structured action plan containing handling contacts and severity levels.
    """
    from ..retrieval.retrieval_pipeline import RetrievalPipeline
    import json
    
    # 1. Map complaint type to a semantically rich query
    query_mapping = {
        "maintenance": "hostel maintenance plumber electrician supervisor HMC hmc@dau.ac.in floor register",
        "mess": "hostel mess committee supervisor food hygiene complaints mess menu contact",
        "ragging": "anti ragging vigilance committee resident warden legal expulsion emergency action",
        "disciplinary": "disciplinary action committee hostel conduct rules fine room dispute warden",
        "general": "hostel room allotment supervisor wardens contact HoR HoR hostel life HMC"
    }
    
    search_query = query_mapping.get(complaint_type.lower(), "hostel rules supervisor warden HMC contacts")
    
    # 2. Query the Knowledge Base (RAG)
    try:
        retrieval_res = RetrievalPipeline().get_context(search_query)
        context = retrieval_res.get("context", "")
    except Exception as e:
        context = ""
        
    if not context.strip():
        # Fallback if KB retrieval is completely empty
        return {
            "handling_contacts": [
                {
                    "name": "Dr. Madhu Kant Sharma",
                    "role": "Resident Warden",
                    "email": "resi_warden@dau.ac.in",
                    "phone": "(+91) 079-68261554"
                }
            ],
            "procedure": [
                "Submit a written complaint in the concerned block register.",
                "If unresolved, escalate to the Hostel Supervisor or Resident Warden."
            ],
            "remedy_timeframe": "Escalate to wardens if unresolved within 24-48 hours.",
            "severity_level": "normal"
        }

    # 3. Use LLM to extract structured fields from the retrieved KB context
    system_prompt = """
You are an information extraction assistant for Dhirubhai Ambani University.
Your task is to read the retrieved hostel rules and directory context, and extract details about how a student can file a specific complaint.

Extract the following fields from the context:
1. handling_contacts: A list of contacts responsible for this complaint (e.g. Wardens, HMC, Supervisors, Anti-Ragging Committee members). For each contact, extract: name, role (title), email, and phone number (if available).
2. procedure: A list of step-by-step actions/guidelines the student must follow to file this complaint (e.g., write in register, contact supervisor, email warden).
3. remedy_timeframe: Estimated resolution times or escalation timelines mentioned in the text.
4. severity_level: Classify the complaint severity as either "high" (for ragging, critical medical cases, severe disciplinary actions) or "normal" (for maintenance, mess, room allotment).

Output ONLY valid JSON matching this format (no markdown code blocks, no additional text):
{
  "handling_contacts": [
    {"name": "Name...", "role": "Role...", "email": "Email...", "phone": "Phone..."}
  ],
  "procedure": ["step 1", "step 2"],
  "remedy_timeframe": "Escalation/resolution timeline details...",
  "severity_level": "high" | "normal"
}
"""

    user_content = f"Complaint Type: {complaint_type}\n\nRetrieved Guidelines Context:\n{context}"

    try:
        client = _get_groq_client()
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_content}
            ]
        )
        
        raw_content = response.choices[0].message.content.strip()
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(raw_content)
        
        if not isinstance(parsed.get("handling_contacts"), list):
            parsed["handling_contacts"] = []
        if not isinstance(parsed.get("procedure"), list):
            parsed["procedure"] = [str(parsed.get("procedure", "Submit complaint through official channels."))]
            
        parsed.setdefault("remedy_timeframe", "Escalate if unresolved within 48 hours.")
        parsed.setdefault("severity_level", "normal")
        
        audit_log(identity, query=f"get_hostel_complaint_guidance:{complaint_type}", allowed=True, target="kb")
        return parsed
        
    except Exception as e:
        audit_log(identity, query=f"get_hostel_complaint_guidance:{complaint_type}", allowed=False, target="kb", reason=str(e))
        return {
            "handling_contacts": [
                {
                    "name": "Dr. Madhu Kant Sharma",
                    "role": "Resident Warden",
                    "email": "resi_warden@dau.ac.in",
                    "phone": "(+91) 079-68261554"
                }
            ],
            "procedure": [
                "Report the issue to the Hostel Supervisor or Resident Warden immediately."
            ],
            "remedy_timeframe": "Escalate to warden if unresolved.",
            "severity_level": "normal"
        }


def screen_scholarship_eligibility(identity, branch: str, year: int, category: str, cgpa: float, annual_income: float = None, **kwargs) -> dict:
    """
    Retrieves the scholarship rules from the KB and cross-references them against the student's profile
    attributes (branch, year, category, cgpa, annual_income) to evaluate eligibility dynamically.
    """
    from ..retrieval.retrieval_pipeline import RetrievalPipeline
    import json
    
    # 1. Query the Knowledge Base (RAG)
    search_query = "scholarships and financial aid eligibility conditions criteria merit cum means JEE rank DAFS Cybage Satnaam"
    try:
        retrieval_res = RetrievalPipeline().get_context(search_query)
        context = retrieval_res.get("context", "")
    except Exception as e:
        context = ""
        
    if not context.strip():
        # Fallback if KB retrieval is completely empty
        return {
            "eligible_schemes": [
                {
                    "name": "Merit Scholarship",
                    "type": "Merit-based",
                    "benefit": "Full or partial tuition fee reimbursement",
                    "status": "conditionally_eligible",
                    "reason_or_conditions": f"Requires being in the top SPI performers of the semester. Your current CGPA/CPI is {cgpa}.",
                    "mandatory_documents": ["Semester Grade Card / Mark Sheet"],
                    "deadline": "Refer to Academic Office"
                }
            ],
            "general_guidelines": [
                "Must maintain minimum SPI/CPI as specified.",
                "No backlogs in any credit course.",
                "No disciplinary proceedings against the student.",
                "All fees must be paid by the due date."
            ]
        }

    # 3. Use LLM to cross-reference student profile against the KB rules
    system_prompt = """
You are a scholarship screening assistant for Dhirubhai Ambani University.
Your task is to read the retrieved university guidelines context containing scholarship schemes and cross-reference them against the student's profile attributes.

Student Profile:
- Branch/Program: {branch}
- Current Year of Study: {year}
- Admission Category: {category}
- Current CGPA/CPI: {cgpa}
- Annual Family Income (INR): {annual_income}

For each scholarship scheme mentioned in the context (e.g. Merit Scholarship, Merit-cum-Means, UG/BS+MS Fellowship, DAFS, Cybage Khushboo, Satnaam WaheGuruji, etc.), evaluate the student's eligibility and output a structured list.

Fields to return for each scheme:
1. name: The name of the scholarship scheme.
2. type: The type of scholarship (e.g., "Merit-based", "Merit-cum-Means", "External", "Fellowship").
3. benefit: The benefit of the scholarship (e.g. tuition fee waiver details).
4. status: Classify status as "eligible" (meets all criteria), "conditionally_eligible" (meets some criteria but requires actions like income certificate verification or being in top performers), or "ineligible" (fails basic eligibility like CGPA/CPI threshold or branch/category requirements).
5. reason_or_conditions: A clear explanation of why they got this status and what conditions they must meet.
6. mandatory_documents: List of documents required to apply for this scheme.
7. deadline: The deadline mentioned in the context, or "Refer to Academic Office" if not specified.

Also extract "general_guidelines" containing general rules (e.g. no backlogs, no disciplinary actions, fee payment rules).

Output ONLY valid JSON matching this format (no markdown code blocks, no additional text):
{{
  "eligible_schemes": [
    {{
      "name": "Scheme Name",
      "type": "Type...",
      "benefit": "Benefit...",
      "status": "eligible" | "conditionally_eligible" | "ineligible",
      "reason_or_conditions": "Reason...",
      "mandatory_documents": ["doc1", "doc2"],
      "deadline": "Deadline..."
    }}
  ],
  "general_guidelines": ["guideline 1", "guideline 2"]
}}
"""

    formatted_prompt = system_prompt.format(
        branch=branch,
        year=year,
        category=category,
        cgpa=cgpa,
        annual_income=annual_income if annual_income is not None else "Not provided"
    )

    user_content = f"Retrieved Guidelines Context:\n{context}"

    try:
        client = _get_groq_client()
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": formatted_prompt.strip()},
                {"role": "user", "content": user_content}
            ]
        )
        
        raw_content = response.choices[0].message.content.strip()
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(raw_content)
        
        if not isinstance(parsed.get("eligible_schemes"), list):
            parsed["eligible_schemes"] = []
        if not isinstance(parsed.get("general_guidelines"), list):
            parsed["general_guidelines"] = ["Must have no backlogs.", "No disciplinary proceedings."]
            
        audit_log(identity, query=f"screen_scholarship_eligibility:{branch}:{category}:{cgpa}", allowed=True, target="kb")
        return parsed
        
    except Exception as e:
        audit_log(identity, query=f"screen_scholarship_eligibility:{branch}:{category}:{cgpa}", allowed=False, target="kb", reason=str(e))
        return {
            "eligible_schemes": [
                {
                    "name": "Merit Scholarship",
                    "type": "Merit-based",
                    "benefit": "Full or partial tuition fee reimbursement",
                    "status": "conditionally_eligible",
                    "reason_or_conditions": f"Requires being in the top SPI performers of the semester. Your CGPA is {cgpa}.",
                    "mandatory_documents": ["Grade card / Mark sheet"],
                    "deadline": "Refer to Academic Office"
                }
            ],
            "general_guidelines": [
                "Must maintain minimum SPI/CPI as specified.",
                "No backlogs in any credit course.",
                "No disciplinary proceedings against the student."
            ]
        }
