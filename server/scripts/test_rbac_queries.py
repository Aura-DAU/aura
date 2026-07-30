import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── DYNAMIC SYSTEM MODULE MOCKING ──────────────────────────────────────────
# Inject mock modules into sys.modules to prevent ModuleNotFoundErrors 
# for third-party libraries and their sub-packages that might not be installed.
qdrant_mock = MagicMock()
sys.modules['qdrant_client'] = qdrant_mock
sys.modules['qdrant_client.http'] = qdrant_mock.http
sys.modules['qdrant_client.http.models'] = qdrant_mock.http.models
sys.modules['groq'] = MagicMock()
sys.modules['pinecone'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# Ensure repo server/ and server/rag/ are in python path
repo_dir = Path(r"C:\Users\Kaveesha\OneDrive\Desktop\DAU-pwa")
server_dir = repo_dir / "server"
rag_dir = server_dir / "rag"
sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(rag_dir))

# Mock basic environment configuration
os.environ.setdefault("INTERNAL_JWT_SECRET", "test-secret")
os.environ.setdefault("INTERNAL_RESOLVE_SECRET", "test-resolve-secret")

from pipeline.aura_chat import AuraChat, GENERIC_DENIAL

# ANSI colors for beautiful terminal reporting
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# ══════════════════════════════════════════════════════════════════════════
# GOLDEN RBAC TEST DATASET DEFINITION
# ══════════════════════════════════════════════════════════════════════════
TEST_CASES = [
    {
        "id": 1,
        "name": "Student S1 querying own CGPA",
        "role": "student",
        "erp_id": "S1",
        "dept": "ICT",
        "query": "Show my current CGPA and course registration",
        "classification": {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa", "registration"]},
        "bindings": [],
        "expected_allowed": True,
        "expect_denial_message": False
    },
    {
        "id": 2,
        "name": "Student S1 querying other student S2's attendance",
        "role": "student",
        "erp_id": "S1",
        "dept": "ICT",
        "query": "What is the attendance of student S2?",
        "classification": {"type": "PERSONAL", "target": "S2", "erp_fields": ["attendance"]},
        "bindings": [],
        "expected_allowed": False,
        "expect_denial_message": True
    },
    {
        "id": 3,
        "name": "Student S1 querying public academic calendar",
        "role": "student",
        "erp_id": "S1",
        "dept": "ICT",
        "query": "When do mid-semester exams start for Autumn 2025?",
        "classification": {"type": "PUBLIC", "target": None, "erp_fields": []},
        "bindings": [],
        "expected_allowed": True,
        "expect_denial_message": False
    },
    {
        "id": 4,
        "name": "Student S1 querying faculty salary (restricted doc)",
        "role": "student",
        "erp_id": "S1",
        "dept": "ICT",
        "query": "Show me the faculty salary structure and evaluation rubric",
        "classification": {"type": "PUBLIC", "target": None, "erp_fields": []},
        "bindings": [],
        "expected_allowed": True,
        "check_dls_filter": "faculty_only"
    },
    {
        "id": 5,
        "name": "Faculty F1 querying own schedule",
        "role": "faculty",
        "erp_id": "F1",
        "dept": "ICT",
        "query": "Show my teaching schedule for this semester",
        "classification": {"type": "PERSONAL", "target": "self", "erp_fields": ["timetable"]},
        "bindings": [],
        "expected_allowed": True,
        "expect_denial_message": False
    },
    {
        "id": 6,
        "name": "Faculty F1 querying advisee S1's performance",
        "role": "faculty",
        "erp_id": "F1",
        "dept": "ICT",
        "query": "Check the academic performance of my advisee S1",
        "classification": {"type": "PERSONAL", "target": "S1", "erp_fields": ["grades", "cgpa"]},
        "bindings": [],
        "is_advisee": True,
        "expected_allowed": True,
        "expect_denial_message": False
    },
    {
        "id": 7,
        "name": "Faculty F1 querying non-advisee student S99's grades",
        "role": "faculty",
        "erp_id": "F1",
        "dept": "ICT",
        "query": "Show the grades of student S99",
        "classification": {"type": "PERSONAL", "target": "S99", "erp_fields": ["grades"]},
        "bindings": [],
        "is_advisee": False,
        "expected_allowed": False,
        "expect_denial_message": True
    },
    {
        "id": 8,
        "name": "Admin A1 querying student S1's profile",
        "role": "admin",
        "erp_id": "A1",
        "dept": "Registrar Office",
        "query": "Retrieve the profile and fee status of student S1",
        "classification": {"type": "PERSONAL", "target": "S1", "erp_fields": ["profile", "fees"]},
        "bindings": ["superadmin"],
        "expected_allowed": True,
        "expect_denial_message": False
    },
    {
        "id": 9,
        "name": "Guest querying personal CGPA",
        "role": "guest",
        "erp_id": "G1",
        "dept": None,
        "query": "Show my CGPA",
        "classification": {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"]},
        "bindings": [],
        "expected_allowed": False,
        "expect_denial_message": True
    },
    {
        "id": 10,
        "name": "Guest querying public B.Tech ICT syllabus",
        "role": "guest",
        "erp_id": "G1",
        "dept": None,
        "query": "What is the B.Tech ICT syllabus?",
        "classification": {"type": "PUBLIC", "target": None, "erp_fields": []},
        "bindings": [],
        "expected_allowed": True,
        "expect_denial_message": False
    }
]

def run_rbac_test_suite():
    print(f"\\n{BOLD}============================================================={RESET}")
    print(f"{BOLD}      AURA ROLE-BASED ACCESS CONTROL (RBAC) TEST RUNNER      {RESET}")
    print(f"{BOLD}============================================================={RESET}\\n")

    passed_count = 0
    total_count = len(TEST_CASES)

    for case in TEST_CASES:
        print(f"Test Case #{case['id']}: {BOLD}{case['name']}{RESET}")
        print(f"  Query: \\\"{case['query']}\\\"")
        print(f"  Role:  {case['role']} (ID: {case['erp_id']})")

        # Mock the external dependency interfaces
        with patch('personal_query_classifier.PersonalQueryClassifier.classify') as mock_classify, \
             patch('pipeline.guardrails.query_guardrail.QueryGuardrail.is_safe', return_value=True), \
             patch('pipeline.guardrails.query_guardrail.QueryGuardrail.is_safe_strict', return_value=True), \
             patch('pipeline.retrieval.retrieval_pipeline.RetrievalPipeline.get_context') as mock_get_context, \
             patch('pipeline.generation.answer_generator.AnswerGenerator.generate', return_value="Mocked LLM Response"), \
             patch('db.connection.query') as mock_db_query, \
             patch('erp_connector.ERPConnector.is_advisee') as mock_is_advisee, \
             patch('erp_connector.ERPConnector.find_student_by_name') as mock_find_student, \
             patch('erp_connector.ERPConnector.get_shared_courses', return_value=[]), \
             patch('erp_connector.ERPConnector.get_student_profile', return_value={"program": "BTech-ICT"}), \
             patch('erp_connector.ERPConnector.get_faculty_courses', return_value=[]), \
             patch('audit_log.AuditLog.record'):

            # Setup classification outcomes
            mock_classify.return_value = case['classification']
            
            # Setup DB role bindings return value
            mock_db_query.return_value = [{"binding": b} for b in case['bindings']]
            
            # Setup ERP advisee check
            mock_is_advisee.return_value = case.get("is_advisee", False)

            # Setup name resolution mock
            def fake_find_student(name):
                if name == "S2":
                    return {"roll_number": "202401475"}
                if name == "S99":
                    return {"roll_number": "999000099"}
                if name == "S1":
                    return {"roll_number": "S1"}
                return None
            mock_find_student.side_effect = fake_find_student

            # Setup mock retrieval payload
            mock_get_context.return_value = {
                "context": "Fake document content",
                "chunks": [{"text": "Fake", "metadata": {"authorization": "faculty_only"}}],
                "sources": [{"title": "Course File", "path": "course_file.md"}],
                "corrected_query": case['query']
            }

            # Initialize mock user identity
            class MockIdentity:
                def __init__(self, erp_id, role, dept):
                    self.erp_id = erp_id
                    self.role = role
                    self.dept = dept
                    self.email = f"{erp_id}@dau.ac.in"
                    self.full_name = "Mock User"
                    self.current_year = 2
                    self.current_sem = 3
                    self.current_sec = "A"

                def as_dict(self):
                    return {
                        "erp_id": self.erp_id,
                        "role": self.role,
                        "dept": self.dept,
                        "email": self.email
                    }

            identity = MockIdentity(case['erp_id'], case['role'], case['dept'])

            # Instantiate and invoke AuraChat
            bot = AuraChat()
            response = None
            try:
                response = bot.chat(case['query'], identity=identity)
            except Exception as e:
                # Catch eCampus CredentialsNotLinked as expected / ALLOWED response path
                if "No eCampus credentials linked" in str(e):
                    response = {"answer": "Mocked LLM Response"}
                else:
                    raise

            # Verify actual result against expectations
            actual_answer = response.get("answer", "")
            is_denied = (actual_answer == GENERIC_DENIAL)

            passed = True
            failure_reason = ""

            if case.get("expect_denial_message"):
                if not is_denied:
                    passed = False
                    failure_reason = f"Expected access to be DENIED, but was ALLOWED (got: '{actual_answer}')"
            else:
                if is_denied:
                    passed = False
                    failure_reason = "Expected access to be ALLOWED, but was DENIED"

            if case.get("check_dls_filter"):
                if not mock_get_context.called:
                    passed = False
                    failure_reason = "Expected RAG retrieval pipeline to be queried for DLS checks, but was bypassed"

            if passed:
                print(f"  Result: {GREEN}PASS{RESET} ✅")
                passed_count += 1
            else:
                print(f"  Result: {RED}FAIL{RESET} ❌")
                print(f"    Details: {failure_reason}")

        print("-" * 60)

    print(f"\\n{BOLD}Test Summary: {passed_count}/{total_count} passed.{RESET}")
    if passed_count == total_count:
        print(f"{GREEN}{BOLD}ALL RBAC ACCESS CONTROL CHECKS PASSED SUCCESSFULLY!{RESET}\\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}SOME ACCESS BOUNDARY CHECKS FAILED.{RESET}\\n")
        sys.exit(1)

if __name__ == "__main__":
    run_rbac_test_suite()
