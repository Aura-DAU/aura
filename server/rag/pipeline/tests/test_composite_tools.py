import pytest
from pipeline.ecampus import composite_tools
from pipeline.ecampus import credentials_vault as vault
from pipeline.ecampus import cache
from pipeline.ecampus.credentials_vault import CredentialsNotLinked
from pipeline.personal_data.access_control import AccessDenied


class FakeECampusClient:
    """Stand-in for the real scraping client — returns canned data instead
    of touching ecampus.daiict.ac.in. instances_by_erp_id lets a test control
    exactly what a given erp_id 'has' before constructing the client."""

    instances_by_erp_id = {}

    def __init__(self, erp_id):
        self.erp_id = erp_id
        if erp_id not in FakeECampusClient.instances_by_erp_id:
            raise CredentialsNotLinked(f"No eCampus credentials linked for {erp_id}.")
        self._data = FakeECampusClient.instances_by_erp_id[erp_id]

    def get_attendance(self):
        return self._data.get("attendance", [])

    def get_cgpa(self):
        return self._data.get("cgpa", {})

    def get_fees(self):
        return self._data.get("fees", {})

    def get_hostel(self):
        return self._data.get("hostel", {})

    def get_registration(self):
        return self._data.get("registration", [])

    def get_result(self):
        return self._data.get("result", {"grades": []})


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    FakeECampusClient.instances_by_erp_id = {}
    monkeypatch.setattr(composite_tools, "ECampusClient", FakeECampusClient)
    yield
    for erp_id in ("S1", "S2"):
        for faculty_id in ("F1", "F2"):
            vault.revoke_advisor_consent(erp_id, faculty_id)


def student_identity(erp_id="S1"):
    return {"role": "student", "erp_id": erp_id}


def faculty_identity(erp_id="F1"):
    return {"role": "faculty", "erp_id": erp_id}


# ── check_exam_eligibility ───────────────────────────────────────────────

def test_check_exam_eligibility_flags_low_attendance():
    FakeECampusClient.instances_by_erp_id["S1"] = {
        "attendance": [
            {"course_code": "CS301", "percentage": "82"},
            {"course_code": "CS302", "percentage": "60"},
        ]
    }
    result = composite_tools.check_exam_eligibility(student_identity())
    assert result["eligible_for_all_exams"] is False
    flagged_codes = [c["course_code"] for c in result["at_risk_courses"]]
    assert flagged_codes == ["CS302"]


def test_check_exam_eligibility_all_clear():
    FakeECampusClient.instances_by_erp_id["S1"] = {
        "attendance": [{"course_code": "CS301", "percentage": "90"}]
    }
    result = composite_tools.check_exam_eligibility(student_identity())
    assert result["eligible_for_all_exams"] is True
    assert result["at_risk_courses"] == []


def test_check_exam_eligibility_unlinked_account_returns_action_needed():
    result = composite_tools.check_exam_eligibility(student_identity("S_unlinked"))
    assert result["action_needed"] == "link_ecampus_account"


# ── get_academic_snapshot ────────────────────────────────────────────────

def test_academic_snapshot_combines_all_sources():
    FakeECampusClient.instances_by_erp_id["S1"] = {
        "cgpa": {"cgpa_raw_label": "CGPA: 8.5"},
        "attendance": [{"course_code": "CS301", "percentage": "90"}],
        "fees": {"payments": []},
        "hostel": {"raw_text": "Block A"},
        "registration": [{"course_code": "CS301"}],
    }
    snapshot = composite_tools.get_academic_snapshot(student_identity())
    assert snapshot["cgpa"]["cgpa_raw_label"] == "CGPA: 8.5"
    assert snapshot["hostel"]["raw_text"] == "Block A"
    assert "_partial_errors" not in snapshot


def test_academic_snapshot_unlinked_account():
    result = composite_tools.get_academic_snapshot(student_identity("S_unlinked"))
    assert result["action_needed"] == "link_ecampus_account"


# ── refresh_my_data ───────────────────────────────────────────────────────

def test_refresh_my_data_clears_cache():
    cache.set(cache.cache_key("S1", "/Attendance.aspx"), [{"stale": True}])
    assert cache.get(cache.cache_key("S1", "/Attendance.aspx")) is not None

    composite_tools.refresh_my_data(student_identity())

    assert cache.get(cache.cache_key("S1", "/Attendance.aspx")) is None


# ── consent management ────────────────────────────────────────────────────

def test_student_can_share_and_revoke_advisor_access():
    composite_tools.share_data_with_advisor(student_identity("S1"), faculty_erp_id="F1")
    assert vault.has_advisor_consent("S1", "F1") is True

    listing = composite_tools.list_my_data_sharing(student_identity("S1"))
    assert listing["shared_with"] == ["F1"]

    composite_tools.revoke_advisor_access(student_identity("S1"), faculty_erp_id="F1")
    assert vault.has_advisor_consent("S1", "F1") is False


def test_faculty_cannot_grant_their_own_consent():
    with pytest.raises(AccessDenied):
        composite_tools.share_data_with_advisor(faculty_identity("F1"), faculty_erp_id="F1")


def test_faculty_cannot_list_a_students_sharing_settings():
    with pytest.raises(AccessDenied):
        composite_tools.list_my_data_sharing(faculty_identity("F1"))


# ── get_advisee_snapshot — the consent-gating logic this whole layer exists for ──

def test_advisee_snapshot_denied_without_consent():
    FakeECampusClient.instances_by_erp_id["S1"] = {"cgpa": {}, "attendance": []}
    result = composite_tools.get_advisee_snapshot(faculty_identity("F1"), student_erp_id="S1")
    assert result["action_needed"] == "student_consent_required"


def test_advisee_snapshot_allowed_with_consent():
    FakeECampusClient.instances_by_erp_id["S1"] = {
        "cgpa": {"cgpa_raw_label": "CGPA: 9.0"},
        "attendance": [{"course_code": "CS301", "percentage": "95"}],
    }
    vault.grant_advisor_consent("S1", "F1")
    result = composite_tools.get_advisee_snapshot(faculty_identity("F1"), student_erp_id="S1")
    assert result["cgpa"]["cgpa_raw_label"] == "CGPA: 9.0"


def test_advisee_snapshot_consent_is_per_faculty_member():
    """F1 having consent must not let F2 see the same student's data."""
    FakeECampusClient.instances_by_erp_id["S1"] = {"cgpa": {}, "attendance": []}
    vault.grant_advisor_consent("S1", "F1")
    result = composite_tools.get_advisee_snapshot(faculty_identity("F2"), student_erp_id="S1")
    assert result["action_needed"] == "student_consent_required"


def test_student_cannot_call_advisee_snapshot():
    with pytest.raises(AccessDenied):
        composite_tools.get_advisee_snapshot(student_identity("S1"), student_erp_id="S2")


def test_get_document_request_guidance(monkeypatch):
    class FakeRetrievalPipeline:
        def __init__(self):
            pass
        def get_context(self, query):
            return {
                "context": "Follow these steps to apply for a bonafide certificate: 1. Fill online form. 2. Contact CoE office. 3. Processing takes 2 working days."
            }
            
    import pipeline.retrieval.retrieval_pipeline
    monkeypatch.setattr(pipeline.retrieval.retrieval_pipeline, "RetrievalPipeline", FakeRetrievalPipeline)
    
    class FakeMessage:
        def __init__(self, content):
            self.content = content
            
    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)
            
    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]
            
    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse(
                '{"checklist": ["Fill online form"], "handling_office": "CoE Office", "processing_time": "2 working days", "required_documents_and_fees": "None"}'
            )
            
    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()
            
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = FakeChat()
            
    monkeypatch.setattr(composite_tools, "_get_groq_client", lambda: FakeGroq("fake-api-key"))
    
    result = composite_tools.get_document_request_guidance(
        student_identity(),
        document_type="bonafide"
    )
    
    assert result["checklist"] == ["Fill online form"]
    assert result["handling_office"] == "CoE Office"
    assert result["processing_time"] == "2 working days"


def test_get_hostel_complaint_guidance(monkeypatch):
    class FakeRetrievalPipeline:
        def __init__(self):
            pass
        def get_context(self, query):
            return {
                "context": "For maintenance complaints, write in the register. Escalations go to Dr. Madhu Kant Sharma, Resident Warden at resi_warden@dau.ac.in."
            }
            
    import pipeline.retrieval.retrieval_pipeline
    monkeypatch.setattr(pipeline.retrieval.retrieval_pipeline, "RetrievalPipeline", FakeRetrievalPipeline)
    
    class FakeMessage:
        def __init__(self, content):
            self.content = content
            
    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)
            
    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]
            
    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse(
                '{"handling_contacts": [{"name": "Dr. Madhu Kant Sharma", "role": "Resident Warden", "email": "resi_warden@dau.ac.in", "phone": "079-68261554"}], "procedure": ["Write in register", "Email warden"], "remedy_timeframe": "24 hours", "severity_level": "normal"}'
            )
            
    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()
            
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = FakeChat()
            
    monkeypatch.setattr(composite_tools, "_get_groq_client", lambda: FakeGroq("fake-api-key"))
    
    result = composite_tools.get_hostel_complaint_guidance(
        student_identity(),
        complaint_type="maintenance"
    )
    
    assert len(result["handling_contacts"]) == 1
    assert result["handling_contacts"][0]["name"] == "Dr. Madhu Kant Sharma"
    assert result["procedure"] == ["Write in register", "Email warden"]
    assert result["severity_level"] == "normal"


def test_screen_scholarship_eligibility(monkeypatch):
    class FakeRetrievalPipeline:
        def __init__(self):
            pass
        def get_context(self, query):
            return {
                "context": "Institute offers Merit Scholarship to top SPI performers. Merit-cum-Means offers waiver to students with CGPA > 7.5 and family income < 6 Lakh."
            }
            
    import pipeline.retrieval.retrieval_pipeline
    monkeypatch.setattr(pipeline.retrieval.retrieval_pipeline, "RetrievalPipeline", FakeRetrievalPipeline)
    
    class FakeMessage:
        def __init__(self, content):
            self.content = content
            
    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)
            
    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]
            
    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse(
                '{"eligible_schemes": [{"name": "Merit-cum-Means", "type": "Merit-cum-Means", "benefit": "Partial waiver", "status": "eligible", "reason_or_conditions": "Income is low and CGPA is 8.5", "mandatory_documents": ["Income Certificate"], "deadline": "Refer to Academic Office"}], "general_guidelines": ["No backlogs"]}'
            )
            
    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()
            
    class FakeGroq:
        def __init__(self, api_key):
            self.chat = FakeChat()
            
    monkeypatch.setattr(composite_tools, "_get_groq_client", lambda: FakeGroq("fake-api-key"))
    
    result = composite_tools.screen_scholarship_eligibility(
        student_identity(),
        branch="BTech ICT",
        year=2,
        category="General",
        cgpa=8.5,
        annual_income=500000.0
    )
    
    assert len(result["eligible_schemes"]) == 1
    assert result["eligible_schemes"][0]["name"] == "Merit-cum-Means"
    assert result["eligible_schemes"][0]["status"] == "eligible"
    assert result["general_guidelines"] == ["No backlogs"]
