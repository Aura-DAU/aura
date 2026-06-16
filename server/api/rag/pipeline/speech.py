import os
import json
import whisper
import warnings
from thefuzz import process

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# Hardcoded system fallbacks in case config.json is deleted or corrupted
DEFAULT_VOCAB = "Dhirubhai Ambani University, DA-IICT, Prof. Hemant A. Patil, Prof. Saurabh Tiwari, Souvik Sarkar, Prof. Maniklal Das."
DEFAULT_FACULTY = ["Hemant A. Patil", "Saurabh Tiwari", "Souvik Sarkar", "Maniklal Das"]

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            TARGET_VOCAB = config_data.get("target_vocab", DEFAULT_VOCAB)
            FACULTY_LIST = config_data.get("faculty_list", DEFAULT_FACULTY)
            print("[INFO] Successfully loaded vocabulary configurations from config.json")
    except json.JSONDecodeError as je:
        print(f"[CRITICAL WARNING] config.json is corrupted! Syntax error: {je}")
        print("[INFO] Falling back to default hardcoded system arrays.")
        TARGET_VOCAB = DEFAULT_VOCAB
        FACULTY_LIST = DEFAULT_FACULTY
else:
    print("[WARNING] config.json not found. Creating a default configuration file...")
    try:
        template = {"target_vocab": DEFAULT_VOCAB, "faculty_list": DEFAULT_FACULTY}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2)
        TARGET_VOCAB = DEFAULT_VOCAB
        FACULTY_LIST = DEFAULT_FACULTY
    except Exception as e:
        print(f"[ERROR] Could not auto-create config.json: {e}")
        TARGET_VOCAB = DEFAULT_VOCAB
        FACULTY_LIST = DEFAULT_FACULTY


# --- WHISPER INFERENCE ENGINE ---
print("[INFO] Booting up Whisper AI engine...")
model = whisper.load_model("small")
print("[INFO] Whisper model loaded and ready.")


def clean_transcription(raw_text: str) -> str:
    cleaned_text = raw_text
    
    # 1. IMMEDIATE SHORT-CIRCUIT
    for name in FACULTY_LIST:
        if name in raw_text:
            return cleaned_text 
            
    words = raw_text.split()
    words_to_check = words[:30]
    
    # 2. FIRST-LETTER OPTIMIZATION FILTER
    first_letters = {name[0].lower() for name in FACULTY_LIST if name}
    text_letters = {word[0].lower() for word in words_to_check if word}
    
    if not first_letters.intersection(text_letters):
        return cleaned_text 
        
    # 3. SLIDING WINDOW WITH STRICT THRESHOLD
    for window_size in [3, 2]:
        if len(words_to_check) < window_size:
            continue
            
        for i in range(len(words_to_check) - window_size + 1):
            phrase = " ".join(words_to_check[i:i+window_size])
            
            match = process.extractOne(phrase, FACULTY_LIST)
            
            if match and match[1] >= 85:
                correct_name = match[0]
                cleaned_text = cleaned_text.replace(phrase, correct_name)
                
    return cleaned_text


def transcribe_audio(audio_path: str, initial_prompt: str = None) -> str:
    try:
        active_prompt = initial_prompt if initial_prompt else TARGET_VOCAB
        
        result = model.transcribe(
            audio_path, 
            initial_prompt=active_prompt,
            fp16=False
        )
        
        raw_text = result.get("text", "").strip()
        print(f"[DEBUG] Raw Whisper Output: '{raw_text}'")
        
        final_text = clean_transcription(raw_text)
        print(f"[DEBUG] Final Cleaned Output: '{final_text}'\n")
        
        return final_text

    except Exception as e:
        print(f"[ERROR] Whisper failed to process the audio track: {e}")
        raise e