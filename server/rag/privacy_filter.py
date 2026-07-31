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

# Regex patterns for scanning PII leaks in raw text
STUDENT_ID_PAT = re.compile(r"\b20\d{7}\b", re.IGNORECASE) # e.g. 202401001
MOBILE_PAT = re.compile(r"\b(?:\+91[\s\-]?)?[6-9]\d{9}\b") # e.g. +91 9876543210 or 9876543210
UUID_PAT = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


class ResponsePrivacyFilter:
    """
    Response Privacy Filter & Attribute RBAC Engine.
    Enforces the Principle of Least Disclosure across retrieved context and LLM outputs.
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
        Inspect if the user is explicitly requesting restricted sensitive fields
        (e.g., 'What is the mobile number of the convenor?', 'What is the student ID?').
        
        Returns:
            (is_blocked, refusal_message)
        """
        if not query:
            return False, None

        q_lower = query.lower()

        # Check if query requests mobile / phone number
        requests_mobile = any(term in q_lower for term in ("mobile", "phone", "contact number", "cell number", "whatsapp number"))
        # Check if query requests student ID / roll number
        requests_student_id = any(term in q_lower for term in ("student id", "student number", "roll number", "erp id", "uid"))

        if requests_mobile or requests_student_id:
            if not self.is_authorized:
                refusal = (
                    "Mobile numbers and Student IDs are restricted private records under the university privacy policy "
                    "and cannot be disclosed."
                )
                return True, refusal

        return False, None

    def sanitize_retrieved_context(self, context_text: str) -> str:
        """
        Filter raw text chunks retrieved from vector search to remove embedded PII
        (student IDs, phone numbers, personal emails) unless the user is authorized.
        """
        if not context_text or self.is_authorized:
            return context_text

        sanitized = context_text
        
        # Scrub 9-digit Student IDs when listed as private attributes
        sanitized = re.sub(r"(?i)(?:student\s*id|roll\s*no|roll\s*number|erp\s*id)\s*[:=]?\s*20\d{7}", "[REDACTED_STUDENT_ID]", sanitized)
        # Scrub Mobile Numbers
        sanitized = re.sub(r"(?i)(?:mobile|phone|contact)\s*(?:no|number)?\s*[:=]?\s*(?:\+91[\s\-]?)?[6-9]\d{9}", "[REDACTED_MOBILE_NUMBER]", sanitized)

        return sanitized

    def filter_response_text(self, response_text: str, query: str = "") -> str:
        """
        Post-generation sanitizer: Scans final LLM response text to guarantee no leak
        of restricted attributes (Student ID, Mobile Number, UUIDs). Note: Email addresses are allowed for contact.
        """
        if not response_text or self.is_authorized:
            return response_text

        sanitized = response_text

        # 1. Redact Student IDs if leaked in text
        sanitized = re.sub(r"(?i)(?:student\s*id|roll\s*number|roll\s*no|student\s*#)\s*[:=]?\s*20\d{7}", "Student ID: [REDACTED]", sanitized)
        sanitized = STUDENT_ID_PAT.sub("[REDACTED_ID]", sanitized)

        # 2. Redact Phone / Mobile numbers if leaked in text
        sanitized = re.sub(r"(?i)(?:mobile|phone|contact)\s*(?:number|no)?\s*[:=]?\s*(?:\+91[\s\-]?)?[6-9]\d{9}", "Mobile: [REDACTED]", sanitized)
        sanitized = MOBILE_PAT.sub("[REDACTED_PHONE]", sanitized)

        # 3. Redact UUIDs
        sanitized = UUID_PAT.sub("[REDACTED_UUID]", sanitized)

        return sanitized


def sanitize_response(response_text: str, user_role: str = "student", query: str = "") -> str:
    """Convenience helper to sanitize an LLM output string."""
    privacy_filter = ResponsePrivacyFilter(user_role=user_role)
    return privacy_filter.filter_response_text(response_text, query=query)
