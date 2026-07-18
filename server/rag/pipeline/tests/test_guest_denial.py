"""
v7 regression: guest / no-identity PERSONAL query must return GENERIC_DENIAL
immediately — never crash, never fall through to AccessControlGate/ERP.

Heavy real dependencies (Qdrant-backed RetrievalPipeline, Groq-backed
QueryGuardrail/WellnessGuardrail/AnswerGenerator, ERPConnector) are stubbed
out so this test exercises only aura_chat.py's routing logic, matching the
Fakes-based approach in test_access_gate.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class _FakeClassification:
    @staticmethod
    def classify(query):
        return {"type": "PERSONAL", "target": None}


def _build_aura_chat_with_fakes():
    """Constructs a real AuraChat but with every heavy dependency mocked out,
    so .chat() can be exercised without a DB, Qdrant, or Groq connection."""
    with patch("pipeline.aura_chat.RetrievalPipeline") as MockRP, \
         patch("pipeline.aura_chat.AnswerGenerator") as MockAG, \
         patch("pipeline.aura_chat.QueryGuardrail") as MockGuardrail, \
         patch("pipeline.aura_chat.WellnessGuardrail") as MockWellness, \
         patch("pipeline.aura_chat.ERPConnector") as MockERP, \
         patch("pipeline.aura_chat.PersonalQueryClassifier") as MockClassifier, \
         patch("pipeline.aura_chat.ERPContextBuilder") as MockCtxBuilder, \
         patch("pipeline.aura_chat.AccessControlGate") as MockGate, \
         patch("pipeline.aura_chat.AuditLog") as MockAuditLog:

        MockGuardrail.return_value.is_safe.return_value = True
        MockGuardrail.return_value.is_safe_strict.return_value = True
        MockWellness.return_value.check.return_value = False
        MockClassifier.return_value.classify.side_effect = _FakeClassification.classify
        # If the code under test reaches AccessControlGate.evaluate, that's
        # itself a bug for the guest/no-identity path — make it loud.
        MockGate.return_value.evaluate.side_effect = AssertionError(
            "AccessControlGate.evaluate() must not be called for guest/no-identity PERSONAL queries"
        )

        from pipeline.aura_chat import AuraChat
        return AuraChat()


def test_guest_role_personal_query_returns_generic_denial_not_crash():
    chat = _build_aura_chat_with_fakes()
    result = chat.chat(
        query="What is my CGPA?",
        history=[],
        identity={"erp_id": "GUEST", "role": "guest", "dept": None},
    )
    assert result["answer"]  # non-empty denial message, not a crash
    assert result["sources"] == []
    assert result.get("is_personal_data") is False
    assert "CGPA" not in result["answer"]  # never leaks a hint at real data


def test_no_identity_personal_query_returns_generic_denial_not_crash():
    chat = _build_aura_chat_with_fakes()
    result = chat.chat(
        query="What is my CGPA?",
        history=[],
        identity=None,
    )
    assert result["answer"]
    assert result["sources"] == []
    assert result.get("is_personal_data") is False
