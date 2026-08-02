import os
import json
import re
import logging
import warnings
from typing import Any

from rapidfuzz import process, fuzz

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# CQ-07 fix: moved from api/schemas.py, which should only hold Pydantic
# request/response models. This is domain content specific to Whisper
# transcription (passed as `initial_prompt` below), so it belongs in the
# speech pipeline module that actually uses it.
UNIVERSITY_PROMPT = (
    "Dhirubhai Ambani University, DAU, DA-IICT, Gandhinagar. "
    "B.Tech ICT, B.Tech CS AI, B.Tech ECE, BS-MS, M.Tech, M.Sc, M.Des, Ph.D. "
    "AURA, CGPA, semester, admissions, fees, hostel, scholarship, placement."
)

# System user `aura` has HOME=/nonexistent; Whisper must not write there.
# Prefer WHISPER_CACHE_DIR; default to /tmp so a root-owned vault volume cannot block boot.
_WHISPER_CACHE = os.environ.get("WHISPER_CACHE_DIR", "/tmp/whisper-cache")

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(
        f"Production configuration missing at '{CONFIG_PATH}'. "
        "Server startup aborted to prevent near-empty vocabulary initialization."
    )

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        TARGET_VOCAB = config_data["target_vocab"]
        FACULTY_LIST = config_data["faculty_list"]
        logger.info(f"Successfully loaded {len(FACULTY_LIST)} faculty profiles from config.json")
except (json.JSONDecodeError, KeyError) as e:
    raise RuntimeError(
        f"config.json is corrupted or missing required keys: {e}. "
        "Server startup aborted."
    )

_model: Any | None = None


def _get_model() -> Any:
    """Load Whisper on first /speech call (not at API import / gunicorn boot)."""
    global _model
    if _model is not None:
        return _model
    import whisper

    os.makedirs(_WHISPER_CACHE, exist_ok=True)
    logger.info("Booting up Whisper AI engine (cache=%s)...", _WHISPER_CACHE)
    _model = whisper.load_model("base", download_root=_WHISPER_CACHE)
    logger.info("Whisper base model loaded and ready.")
    return _model


def clean_transcription(raw_text: str) -> str:
    hallucination_words = {"you", "thank", "yeah", "uh", "um"}
    text_clean = raw_text.strip()

    for word in hallucination_words:
        text_clean = re.sub(r'^\b' + re.escape(word) + r'\b\s*', '', text_clean, flags=re.IGNORECASE)

    cleaned_text = text_clean
    words = text_clean.split()
    words_to_check = words[:30]

    already_matched_names = set()
    for name in FACULTY_LIST:
        if name in text_clean:
            already_matched_names.add(name)

    first_letters = {name[0].lower() for name in FACULTY_LIST if name and name not in already_matched_names}
    text_letters = {word[0].lower() for word in words_to_check if word}

    if not first_letters.intersection(text_letters) and not already_matched_names:
        return re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', cleaned_text, flags=re.IGNORECASE)

    substituted_phrases = set()

    for window_size in [3, 2]:
        if len(words_to_check) < window_size:
            continue

        for i in range(len(words_to_check) - window_size + 1):
            raw_phrase = " ".join(words_to_check[i:i+window_size])

            # Strip leading/trailing punctuation for matching, keep track of it
            phrase = raw_phrase.strip(".,!?;:\"'")
            trailing_punct = raw_phrase[len(raw_phrase.rstrip(".,!?;:\"'")):]

            if not phrase:
                continue

            if any(phrase in sub for sub in substituted_phrases):
                continue

            # Stricter scorer + higher threshold to avoid loose partial matches
            match = process.extractOne(phrase, FACULTY_LIST, scorer=fuzz.token_sort_ratio)

            if match and match[1] >= 88:
                correct_name = match[0]

                # Sanity check: reject if word-count difference is too large
                phrase_word_count = len(phrase.split())
                name_word_count = len(correct_name.split())
                if abs(phrase_word_count - name_word_count) > 1:
                    continue

                # Build pattern that matches the original phrase including
                # optional trailing punctuation
                pattern = r'\b' + re.escape(phrase) + r'\b' + re.escape(trailing_punct)
                replacement = correct_name + trailing_punct
                cleaned_text = re.sub(pattern, replacement, cleaned_text)
                substituted_phrases.add(phrase)

    cleaned_text = re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text


def transcribe_audio(audio_path: str, initial_prompt: str = None) -> str:
    try:
        active_prompt = initial_prompt if initial_prompt else TARGET_VOCAB

        result = _get_model().transcribe(
            audio_path,
            initial_prompt=active_prompt,
            fp16=False,
            language="en",
        )
        
        raw_text = result.get("text", "").strip()
        logger.debug(f"Raw Whisper Output: '{raw_text}'")
        
        final_text = clean_transcription(raw_text)
        logger.debug(f"Final Cleaned Output: '{final_text}'")
        
        return final_text

    except Exception:
        logger.error("Whisper failed to process the audio track", exc_info=True)
        raise