from __future__ import annotations
import sys
import unittest
from pathlib import Path

# Add server directory to sys.path
SERVER_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = SERVER_DIR / "rag"
for p in (str(SERVER_DIR), str(RAG_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from institution_resolver import get_institution_resolver, InstitutionResolver
from privacy_filter import ResponsePrivacyFilter, sanitize_response


class TestInstitutionResolverAndPrivacy(unittest.TestCase):

    def setUp(self):
        self.resolver = get_institution_resolver()
        self.student_privacy_filter = ResponsePrivacyFilter(user_role="student")
        self.admin_privacy_filter = ResponsePrivacyFilter(user_role="admin_staff")

    def test_institution_resolver_dadc(self):
        query = "Who is the convenor of DADC?"
        resolved = self.resolver.resolve(query)
        self.assertIn("Dance Club (DADC)", resolved)
        self.assertIn("at DAU", resolved)

    def test_institution_resolver_dance_club(self):
        query = "Tell me about the Dance Club"
        resolved = self.resolver.resolve(query)
        self.assertIn("Dance Club (DADC)", resolved)

    def test_institution_resolver_multiple_aliases(self):
        query = "Where is CDC and Hostel Office located?"
        resolved = self.resolver.resolve(query)
        self.assertIn("Career Development Cell (CDC)", resolved)
        self.assertIn("University Hostel Office", resolved)

    def test_privacy_filter_public_email_allowed(self):
        query = "What is the official email of the convenor?"
        is_blocked, refusal = self.student_privacy_filter.check_explicit_privacy_request(query)
        self.assertFalse(is_blocked)
        self.assertIsNone(refusal)

    def test_privacy_filter_student_id_denied_for_student(self):
        query = "What is the student ID of Vedant?"
        is_blocked, refusal = self.student_privacy_filter.check_explicit_privacy_request(query)
        self.assertTrue(is_blocked)
        self.assertIn("Student IDs are restricted private records", refusal)

    def test_privacy_filter_mobile_number_denied_for_student(self):
        query = "What is the mobile number of the convenor?"
        is_blocked, refusal = self.student_privacy_filter.check_explicit_privacy_request(query)
        self.assertTrue(is_blocked)
        self.assertIn("student ids are restricted private records", refusal.lower())

    def test_privacy_filter_mobile_number_allowed_for_admin(self):
        query = "What is the mobile number of the convenor?"
        is_blocked, refusal = self.admin_privacy_filter.check_explicit_privacy_request(query)
        self.assertFalse(is_blocked)
        self.assertIsNone(refusal)

    def test_context_sanitization_removes_restricted_fields(self):
        profile_obj = {
            "name": "Vedant Shah",
            "role": "Convenor",
            "club": "Dance Club (DADC)",
            "official_email": "vedant@dau.ac.in",
            "student_id": "202601001",
            "mobile": "9876543210",
            "erp_id": "ERP998877"
        }
        sanitized = self.student_privacy_filter.sanitize_context_object(profile_obj)
        self.assertIn("name", sanitized)
        self.assertIn("official_email", sanitized)
        self.assertNotIn("student_id", sanitized)
        self.assertNotIn("mobile", sanitized)
        self.assertNotIn("erp_id", sanitized)

    def test_post_generation_pii_redaction(self):
        leaked_response = (
            "The convenor of the Dance Club (DADC) is Vedant Shah.\n"
            "Faculty Mentor: Sreeja Rajendran.\n"
            "Student ID: 202601001\n"
            "Mobile: 9876543210\n"
            "Official Email: vedant@dau.ac.in"
        )
        cleaned = self.student_privacy_filter.filter_response_text(leaked_response)
        self.assertIn("Vedant Shah", cleaned)
        self.assertIn("Sreeja Rajendran", cleaned)
        self.assertIn("vedant@dau.ac.in", cleaned)
        self.assertNotIn("202601001", cleaned)
    def test_helpline_and_emergency_contacts_allowed(self):
        query = "What is the emergency helpline number for security?"
        is_blocked, refusal = self.student_privacy_filter.check_explicit_privacy_request(query)
        self.assertFalse(is_blocked)
        self.assertIsNone(refusal)

        helpline_response = (
            "DAU Emergency Helplines & Security Desk Contacts:\n"
            "- Campus Security Desk: 079-68261700 / +91-9876543210\n"
            "- Medical Emergency Desk: 079-68261701\n"
            "- National Anti-Ragging Helpline: 1800-180-5522"
        )
        cleaned = self.student_privacy_filter.filter_response_text(helpline_response, query=query)
        self.assertIn("079-68261700", cleaned)
        self.assertIn("1800-180-5522", cleaned)


if __name__ == "__main__":
    unittest.main()
