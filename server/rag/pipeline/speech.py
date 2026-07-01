import os
import json
import re
import logging
import whisper
import warnings
import torch
import threading
import asyncio
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
from rapidfuzz import process, fuzz

# Load environment variables dynamically from server/rag/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

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

def normalize_name(name):
    # Remove single letters followed by optional dot, e.g. 'A.', 'P ', ' J'
    name_clean = re.sub(r'\b[a-zA-Z]\.?(?:\s+|$)', '', name)
    return ' '.join(name_clean.split())

FACULTY_LOOKUP = {}
for name in FACULTY_LIST:
    FACULTY_LOOKUP[name.lower()] = name
    norm = normalize_name(name)
    if norm.lower() != name.lower() and len(norm.split()) >= 1:
        FACULTY_LOOKUP[norm.lower()] = name

_local_model = None
_local_model_lock = threading.Lock()

def get_local_model():
    global _local_model
    if _local_model is None:
        with _local_model_lock:
            if _local_model is None:
                logger.info("Booting up local Whisper AI engine...")
                env_device = os.getenv("WHISPER_DEVICE")
                if env_device:
                    device = env_device
                elif torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
                _local_model = whisper.load_model("base", device=device)
                logger.info(f"Whisper base model loaded on {device} and ready.")
    return _local_model


local_fallback_semaphore = asyncio.Semaphore(1)


def clean_transcription(raw_text: str) -> str:
    # Deterministic/looping start filler & silence cleanup
    text_clean = raw_text.strip()
    while True:
        new_text = re.sub(r'^(?:you|thank|yeah|uh|um|thank\s+you)\b\s*[.,?!;:]*\s*', '', text_clean, flags=re.IGNORECASE)
        if new_text == text_clean:
            break
        text_clean = new_text

    # Clean standard Whisper trailing hallucinations
    hallucination_ends = [
        r'\bthank\s+you\s+for\s+watching\b\.?$',
        r'\bplease\s+subscribe\s+to\s+my\s+channel\b\.?$',
        r'\bsubscribe\s+to\s+my\s+channel\b\.?$',
        r'\bthank\s+you\s+very\s+much\b\.?$',
        r'\bthank\s+you\b\.?$'
    ]
    for pattern in hallucination_ends:
        text_clean = re.sub(pattern, '', text_clean, flags=re.IGNORECASE).strip()

    cleaned_text = text_clean
    words = text_clean.split()

    already_matched_names = set()
    for name in FACULTY_LIST:
        if name in text_clean:
            already_matched_names.add(name)

    first_letters = {name[0].lower() for name in FACULTY_LIST if name and name not in already_matched_names}
    cleaned_words = [re.sub(r'^[^a-zA-Z0-9]+', '', w) for w in words]
    text_letters = {w[0].lower() for w in cleaned_words if w}

    if not first_letters.intersection(text_letters) and not already_matched_names:
        return re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', cleaned_text, flags=re.IGNORECASE)

    substituted_phrases = set()

    for window_size in [3, 2]:
        if len(words) < window_size:
            continue

        for i in range(len(words) - window_size + 1):
            raw_phrase = " ".join(words[i:i+window_size])

            # Strip leading/trailing punctuation for matching, keep track of it
            phrase = raw_phrase.strip(".,!?;:\"'")
            trailing_punct = raw_phrase[len(raw_phrase.rstrip(".,!?;:\"'")):]

            if not phrase:
                continue

            if any(phrase in sub for sub in substituted_phrases):
                continue

            # Stricter scorer + higher threshold to avoid loose partial matches
            match = process.extractOne(phrase.lower(), FACULTY_LOOKUP.keys(), scorer=fuzz.ratio)

            if match and match[1] >= 85:
                matched_key = match[0]
                correct_name = FACULTY_LOOKUP[matched_key]

                # Enforce word count equivalence to prevent swallowing surrounding words
                if len(phrase.split()) != len(matched_key.split()):
                    continue

                # Sanity check: reject if word-count difference is too large compared to correct name
                phrase_word_count = len(phrase.split())
                name_word_count = len(correct_name.split())
                if abs(phrase_word_count - name_word_count) > 1:
                    continue

                # Build pattern that matches the original phrase including
                # optional trailing punctuation
                pattern = r'\b' + re.escape(phrase) + r'\b' + re.escape(trailing_punct)
                replacement = correct_name + trailing_punct
                cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
                substituted_phrases.add(phrase)

    cleaned_text = re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text


async def transcribe_audio(audio_path: str, initial_prompt: str = None) -> str:
    try:
        active_prompt = initial_prompt if initial_prompt else TARGET_VOCAB
        
        # 1. Attempt Groq Whisper API first for fast, offloaded execution
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                logger.info("Transcribing audio via Groq Whisper API...")
                from groq import Groq
                client = Groq(api_key=groq_key)
                with open(audio_path, "rb") as audio_file:
                    # Run the synchronous API call in Starlette threadpool
                    transcription = await run_in_threadpool(
                        client.audio.transcriptions.create,
                        file=(os.path.basename(audio_path), audio_file.read()),
                        model="whisper-large-v3",
                        prompt=active_prompt,
                        language="en",
                        temperature=0.0
                    )
                raw_text = transcription.text.strip()
                logger.info("Groq API transcription successful.")
                logger.debug(f"Raw Groq Output: '{raw_text}'")
                return clean_transcription(raw_text)
            except Exception as e:
                logger.warning(f"Groq Whisper API failed ({e}). Falling back to local Whisper...")

        # 2. Local Fallback (guarded by local fallback semaphore)
        async with local_fallback_semaphore:
            logger.info("Transcribing audio via local Whisper engine...")
            local_model = get_local_model()
            # Run the synchronous/CPU-bound model execution in Starlette threadpool
            import time
            start_t = time.time()
            result = await run_in_threadpool(
                local_model.transcribe,
                audio_path, 
                initial_prompt=active_prompt,
                fp16=(local_model.device.type == "cuda"),
                language="en"
            )
            duration = time.time() - start_t
            logger.info(f"Local Whisper transcription execution finished in {duration:.2f}s")
            
            raw_text = result.get("text", "").strip()
            logger.debug(f"Raw Whisper Output: '{raw_text}'")
            
            final_text = clean_transcription(raw_text)
            logger.debug(f"Final Cleaned Output: '{final_text}'")
            
            return final_text

    except Exception:
        logger.error("Whisper failed to process the audio track", exc_info=True)
        raise