from __future__ import annotations
import re
import json
from typing import Dict, List, Set, Any, Optional, Tuple, Union

# Public fields allowed by default under Principle of Least Disclosure
PUBLIC_FIELDS: Set[str] = {
    "name",
    "position",
    "role",
    "club",
    "committee",
    "department",
    "faculty_mentor",
    "official_email",
    "email",
    "email_id",
    "contact_email",
    "personal_email",
    "office_location",
    "office_room",
    "office_timings",
    "public_responsibilities",
    "designation",
    "academic_year",
    "programme",
    "branch"
}

# Restricted sensitive fields that MUST NOT be disclosed by default
RESTRICTED_FIELDS: Set[str] = {
    "student_id",
    "student_number",
    "roll_number",
    "mobile",
    "mobile_number",
    "phone",
    "phone_number",
    "contact_number",
    "erp_id",
    "uid",
    "auth_id",
    "internal_id",
    "personal_address",
    "address",
    "dob",
    "date_of_birth",
    "emergency_contact",
    "aadhaar_number",
    "pan_number"
}

# Roles authorized to view restricted administrative fields
AUTHORIZED_ROLES: Set[str] = {
    "admin_staff",
    "superadmin",
    "dean_students",
    "dean_academic",
    "registrar"
}

# Keywords for public institutional helplines and emergency services
PUBLIC_HELPLINE_TERMS: Set[str] = {
    "helpline", "emergency", "security", "reception", "desk", "hospital",
    "ambulance", "toll free", "1800", "landline", "office number",
    "medical emergency", "police", "fire", "anti-ragging", "counseling"
}

# Regex patterns for scanning PII leaks in raw text
STUDENT_ID_PAT = re.compile(r"\b20\d{7}\b", re.IGNORECASE) # e.g. 202401001
MOBILE_PAT = re.compile(r"\b(?:\+91[\s\-]?)?[6-9]\d{9}\b") # e.g. +91 9876543210 or 9876543210
UUID_PAT = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


class ResponsePrivacyFilter:
    """
    Response Privacy Filter & Attribute RBAC Engine.
    Enforces the Principle of Least Disclosure across retrieved context and LLM outputs.
    Protects private living entity PII (Student IDs, personal mobile numbers) while preserving
    public institutional helplines, emergency contacts, and desk landlines.
    """

    def __init__(self, user_role: str = "student"):
        self.user_role = user_role.lower() if user_role else "student"
        self.is_authorized = self.user_role in AUTHORIZED_ROLES

    def sanitize_context_object(self, obj: Any) -> Any:
        """
        Recursively strip/redact restricted fields from structured JSON/dict objects
        BEFORE passing context to the LLM prompt.
        """
        if not obj:
            return obj

        if isinstance(obj, dict):
            sanitized = {}
            for k, v in obj.items():
                key_lower = k.lower()
                if not self.is_authorized and key_lower in RESTRICTED_FIELDS:
                    continue  # Strip restricted field entirely
                sanitized[k] = self.sanitize_context_object(v)
            return sanitized

        elif isinstance(obj, list):
            return [self.sanitize_context_object(item) for item in obj]

        return obj

    def check_explicit_privacy_request(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Inspect if the user is explicitly requesting restricted sensitive fields of a living individual
        (e.g., 'What is the mobile number of the convenor?', 'What is the student ID?').
        
        Public helplines, security desks, and emergency contacts are explicitly EXEMPT and ALLOWED.
        """
        if not query:
            return False, None

        q_lower = query.lower()

        # Exempt public institutional helplines & emergency contacts
        if any(term in q_lower for term in PUBLIC_HELPLINE_TERMS):
            return False, None

        # Check if query requests private mobile / phone number of an individual
        requests_mobile = any(term in q_lower for term in ("mobile", "phone", "contact number", "cell number", "whatsapp number"))
        # Check if query requests student ID / roll number
        requests_student_id = any(term in q_lower for term in ("student id", "student number", "roll number", "erp id", "uid"))

        if requests_mobile or requests_student_id:
            if not self.is_authorized:
                refusal = (
                    "Personal mobile numbers and Student IDs are restricted private records under the university privacy policy "
                    "and cannot be disclosed."
                )
                return True, refusal

        return False, None

    def sanitize_retrieved_context(self, context_text: str) -> str:
        """
        Filter raw text chunks retrieved from vector search to remove embedded personal PII
        (student IDs, personal mobile numbers) unless the user is authorized.
        Preserves public helplines and emergency contacts.
        """
        if not context_text or self.is_authorized:
            return context_text

        sanitized = context_text
        
        # Scrub 9-digit Student IDs when listed as private attributes
        sanitized = re.sub(r"(?i)(?:student\s*id|roll\s*no|roll\s*number|erp\s*id)\s*[:=]?\s*20\d{7}", "[REDACTED_STUDENT_ID]", sanitized)
        
        # Scrub personal mobile numbers except lines labeled as helpline/emergency/security/desk
        lines = sanitized.splitlines()
        filtered_lines = []
        for line in lines:
            if any(term in line.lower() for term in PUBLIC_HELPLINE_TERMS) or "1800" in line or "079-" in line:
                filtered_lines.append(line)
            else:
                line_scrubbed = re.sub(r"(?i)(?:mobile|phone|contact)\s*(?:no|number)?\s*[:=]?\s*(?:\+91[\s\-]?)?[6-9]\d{9}", "[REDACTED_MOBILE_NUMBER]", line)
                filtered_lines.append(line_scrubbed)

        return "\n".join(filtered_lines)

    def filter_response_text(self, response_text: str, query: str = "") -> str:
        """
        Post-generation sanitizer: Scans final LLM response text to guarantee no leak
        of living entity PII (Student ID, Personal Mobile Number, UUIDs).
        Preserves public helplines and emergency desk numbers.
        """
        if not response_text or self.is_authorized:
            return response_text

        # If query or response is explicitly about public helplines, exempt text from phone redaction
        q_lower = query.lower()
        resp_lower = response_text.lower()
        if any(term in q_lower or term in resp_lower for term in PUBLIC_HELPLINE_TERMS):
            # Only redact 9-digit Student IDs & UUIDs
            sanitized = re.sub(r"(?i)(?:student\s*id|roll\s*number|roll\s*no|student\s*#)\s*[:=]?\s*20\d{7}", "Student ID: [REDACTED]", response_text)
            sanitized = STUDENT_ID_PAT.sub("[REDACTED_ID]", sanitized)
            sanitized = UUID_PAT.sub("[REDACTED_UUID]", sanitized)
            return sanitized

        sanitized = response_text

        # 1. Redact Student IDs if leaked in text
        sanitized = re.sub(r"(?i)(?:student\s*id|roll\s*number|roll\s*no|student\s*#)\s*[:=]?\s*20\d{7}", "Student ID: [REDACTED]", sanitized)
        sanitized = STUDENT_ID_PAT.sub("[REDACTED_ID]", sanitized)

        # 2. Redact personal Phone / Mobile numbers if leaked in text
        sanitized = re.sub(r"(?i)(?:mobile|phone|contact)\s*(?:number|no)?\s*[:=]?\s*(?:\+91[\s\-]?)?[6-9]\d{9}", "Mobile: [REDACTED]", sanitized)
        sanitized = MOBILE_PAT.sub("[REDACTED_PHONE]", sanitized)

        # 3. Redact UUIDs
        sanitized = UUID_PAT.sub("[REDACTED_UUID]", sanitized)

        return sanitized


def sanitize_response(response_text: str, user_role: str = "student", query: str = "") -> str:
    """Convenience helper to sanitize an LLM output string."""
    privacy_filter = ResponsePrivacyFilter(user_role=user_role)
    return privacy_filter.filter_response_text(response_text, query=query)
