import os
from dotenv import load_dotenv

class KeyManager:
    _keys = []
    _current_idx = 0
    _initialized = False
    
    @classmethod
    def _initialize_keys(cls):
        if cls._initialized:
            return
        load_dotenv()
        
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
        print(f"[KeyManager] Initialized with {len(cls._keys)} keys.")

    @classmethod
    def get_current_key(cls):
        cls._initialize_keys()
        if not cls._keys:
            return os.getenv("GROQ_API_KEY")
        return cls._keys[cls._current_idx]

    @classmethod
    def rotate_key(cls):
        cls._initialize_keys()
        if not cls._keys:
            return os.getenv("GROQ_API_KEY")
            
        cls._current_idx = (cls._current_idx + 1) % len(cls._keys)
        new_key = cls._keys[cls._current_idx]
        # Dynamically override the environment variable so all modules pick it up
        os.environ["GROQ_API_KEY"] = new_key
        print(f"[KeyManager] Rotated to key: ...{new_key[-8:] if new_key else 'None'}")
        return new_key
