import os
import re
import time
import threading
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError
from pipeline.exceptions import RAGPipelineError

class KeyManager:
    _keys = []
    _current_idx = 0
    _initialized = False
    _lock = threading.Lock()
    
    _last_mtime = 0.0

    @classmethod
    def _initialize_keys(cls):
        with cls._lock:
            from pathlib import Path
            env_path = Path(__file__).resolve().parent.parent / ".env"
            
            mtime = 0.0
            if env_path.exists():
                mtime = env_path.stat().st_mtime
                
            if cls._initialized and mtime == cls._last_mtime:
                return
                
            # Override existing environment variables with the newly loaded ones
            load_dotenv(env_path, override=True)
            
            # Reset keys list
            cls._keys = []
            
            # Load primary key
            primary = os.getenv("GROQ_API_KEY")
            if primary:
                cls._keys.append(primary)
                
            # Load secondary keys (GROQ_API_KEY_2, GROQ_API_KEY_3, etc.)
            idx = 2
            while True:
                key = os.getenv(f"GROQ_API_KEY_{idx}")
                if not key:
                    break
                cls._keys.append(key)
                idx += 1
                
            cls._initialized = True
            cls._last_mtime = mtime
            cls._current_idx = 0
            print(f"[KeyManager] Initialized/Reloaded with {len(cls._keys)} keys. (mtime: {mtime})")

    @classmethod
    def get_current_key(cls):
        cls._initialize_keys()
        with cls._lock:
            if not cls._keys:
                return os.getenv("GROQ_API_KEY")
            return cls._keys[cls._current_idx]

    @classmethod
    def rotate_key(cls):
        cls._initialize_keys()
        with cls._lock:
            if not cls._keys:
                return os.getenv("GROQ_API_KEY")
                
            cls._current_idx = (cls._current_idx + 1) % len(cls._keys)
            new_key = cls._keys[cls._current_idx]
            print(f"[KeyManager] Rotated to key index {cls._current_idx}")
            return new_key

    @classmethod
    def key_count(cls):
        cls._initialize_keys()
        with cls._lock:
            return len(cls._keys)

    @classmethod
    def call_with_rotation(cls, fn, max_retries=5, initial_retry_delay=5.0):
        """
        Executes fn(client) using a Groq client instance.
        If Groq rate limits, capacity constraints, or connection/timeout errors are hit:
          - Automatically rotates the key for daily limits (TPD/RPD) and retries.
          - Backs off exponentially and retries for transient limits.
        Raises RAGPipelineError when all options are exhausted.
        """
        cls._initialize_keys()
        
        # Keep track of keys tried in this request to avoid infinite loops
        keys_tried = set()
        
        retry_delay = initial_retry_delay
        attempt = 0
        
        # Instantiate the client once initially
        current_key = cls.get_current_key()
        client = Groq(api_key=current_key)
        
        while attempt < max_retries:
            try:
                return fn(client)
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                status_code = getattr(e, "status_code", None)
                error_msg = str(e).lower()
                
                # Check for daily-limit detection
                is_daily_limit = False
                if status_code == 429:
                    # A 429 with "try again in Xs" is a burst/minute limit —
                    # back off and retry WITHOUT rotating the key, to avoid
                    # wasting the backup key's burst budget unnecessarily.
                    # Only explicit TPD/RPD keywords should trigger key rotation.
                    is_minute_burst = bool(
                        re.search(r"try again in (\d+(?:\.\d+)?)s", error_msg)
                    )
                    is_daily_limit = (
                        not is_minute_burst and
                        ("tpd" in error_msg or "tokens per day" in error_msg or
                         "rpd" in error_msg or "requests per day" in error_msg)
                    )
                
                if is_daily_limit:
                    with cls._lock:
                        keys_tried.add(current_key)
                        if len(keys_tried) >= len(cls._keys):
                            print("[KeyManager] All API keys exhausted for daily limits. Failing request.")
                            raise RAGPipelineError(f"All API keys exhausted for daily limits: {e}") from e
                        
                    print(f"[KeyManager] Daily rate limit hit: {e}. Rotating API key...")
                    current_key = cls.rotate_key()
                    # Re-instantiate the client only on key rotation
                    client = Groq(api_key=current_key)
                    continue
                
                is_retryable = (status_code in [429, 500, 502, 503, 504]) or isinstance(e, APIConnectionError)
                if is_retryable:
                    if attempt == max_retries - 1:
                        print("[KeyManager] Max retries reached. Failing request.")
                        raise RAGPipelineError(f"Max retries reached: {e}") from e
                    
                    retry_after = retry_delay
                    match = re.search(r"try again in (\d+(?:\.\d+)?)s", error_msg)
                    if match:
                        retry_after = float(match.group(1)) + 1.0  # Add 1s buffer
                    
                    retry_after = min(retry_after, 65.0)
                    print(f"[KeyManager] API error/timeout {status_code}: {e}. Retrying in {retry_after:.2f} seconds...")
                    time.sleep(retry_after)
                    retry_delay *= 2
                    attempt += 1
                else:
                    raise RAGPipelineError(f"API request failed with unretryable status {status_code}: {e}") from e
        
        raise RAGPipelineError("Max retries exceeded with all keys.")
