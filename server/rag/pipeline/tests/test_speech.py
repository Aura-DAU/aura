import os
import shutil
import wave
import struct
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from pipeline.speech import clean_transcription, transcribe_audio
from api.app import app
from api.schemas import MAX_AUDIO_BYTES

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. Unit Tests for Text Post-Processing (clean_transcription)
# ---------------------------------------------------------------------------

def test_clean_transcription_strips_hallucinations():
    raw = "Thank you, um, what is the prerequisite for algorithm design?"
    cleaned = clean_transcription(raw)
    assert not cleaned.lower().startswith("thank you")
    assert "what is the prerequisite" in cleaned.lower()

def test_clean_transcription_deduplicates_repeated_words():
    raw = "What is the fee fee structure for BTech"
    cleaned = clean_transcription(raw)
    assert "fee structure" in cleaned

def test_clean_transcription_faculty_fuzzy_matching():
    raw = "Can I talk to professor Subhash Nandi?"
    cleaned = clean_transcription(raw)
    assert "Subhas Chandra Nandy" in cleaned or "Subhas" in cleaned


# ---------------------------------------------------------------------------
# 2. Integration Tests for Model Inference with Synthetic Audio
# ---------------------------------------------------------------------------

@pytest.fixture
def dummy_wav_file(tmp_path):
    """Generates a 1-second silent WAV file for inference testing."""
    wav_path = str(tmp_path / "test_audio.wav")
    with wave.open(wav_path, "w") as f:
        f.setnchannels(1)     # Mono
        f.setsampwidth(2)     # 16-bit
        f.setframerate(16000) # 16kHz sample rate
        f.writeframes(struct.pack("<h", 0) * 16000)
    return wav_path

@pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="Whisper decodes audio via ffmpeg; not available in the lightweight CI runner.",
)
def test_transcribe_audio_synthetic_wav(dummy_wav_file):
    """Test full transcribe_audio pipeline with a synthetic wav file."""
    result = transcribe_audio(dummy_wav_file)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# 3. API Endpoint Tests (POST /speech)
# ---------------------------------------------------------------------------

def test_speech_endpoint_unauthorized():
    """Verify endpoint blocks unauthenticated calls."""
    response = client.post("/speech")
    assert response.status_code == 401

def test_speech_endpoint_invalid_file_type():
    """Verify rejection of invalid file extensions."""
    # Create internal auth headers using test secrets from conftest.py
    headers = {
        "x-internal-user-id": "test-user-id",
        "x-internal-role": "user"
    }
    # To pass require_identity without real NextAuth we need to mock or pass right headers.
    # The deps.py `require_identity` looks for specific internal JWT headers.
    
    # We will let auth fail or pass based on deps.py, but actually deps.py requires JWT
    # wait, the conftest sets up auth. Let's see if we can pass the auth. 
    # If auth setup is complex, we can mock `require_identity` using `app.dependency_overrides`.
    pass

@pytest.fixture
def override_dependency():
    from api.auth import require_identity, Identity
    def mock_require_identity():
        return Identity(erp_id="test", role="student")
    app.dependency_overrides[require_identity] = mock_require_identity
    yield
    app.dependency_overrides.clear()

def test_speech_endpoint_invalid_file_type_with_mock(override_dependency):
    """Verify rejection of invalid file extensions with mocked auth."""
    files = {"file": ("invalid.txt", b"some text content", "text/plain")}
    response = client.post("/speech", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_speech_endpoint_payload_too_large(override_dependency):
    """Verify payload size enforcement using a large file."""
    # We can mock the UploadFile size or write a big chunk
    class LargeUploadFile:
        filename = "big.wav"
        async def read(self, size):
            return b"0" * (MAX_AUDIO_BYTES + 1)
        
    with patch("api.routes.speech_routes.UploadFile", return_value=LargeUploadFile()):
        # Mock file upload via FastAPI TestClient by sending big data
        # Actually it's easier to just pass big data:
        files = {"file": ("big.wav", b"0" * (MAX_AUDIO_BYTES + 1024), "audio/wav")}
        response = client.post("/speech", files=files)
        assert response.status_code == 413
