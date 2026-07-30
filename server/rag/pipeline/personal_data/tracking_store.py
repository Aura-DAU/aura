"""
File-based JSON store for flexible key-value tracking of non-sensitive user facts
(e.g., DOB, age, interests) as requested by the user.
"""

import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)

# Store in server/data directory
_STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "tracking_flags.json"
)

def _read_store() -> dict:
    if not os.path.exists(_STORE_PATH):
        return {}
    try:
        with open(_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read tracking store: %s", e)
        return {}

def _write_store(store: dict) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    tmp_path = f"{_STORE_PATH}.{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        os.replace(tmp_path, _STORE_PATH)
    except Exception as e:
        logger.error("Failed to write tracking store: %s", e)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to remove temporary tracking store file '%s': %s",
                    tmp_path,
                    cleanup_error,
                )

def get_tracking_flags(erp_id: str) -> dict:
    """Returns the tracked facts for the given user."""
    if not erp_id:
        return {}
    store = _read_store()
    return store.get(str(erp_id), {})

def update_tracking_flags(erp_id: str, new_flags: dict) -> dict:
    """
    Updates the tracked facts for the user by merging new_flags into existing flags.
    Returns the updated flags dict.
    """
    if not erp_id:
        return {}
        
    store = _read_store()
    user_flags = store.get(str(erp_id), {})
    
    # Merge
    for k, v in new_flags.items():
        if v is None:
            user_flags.pop(k, None)
        else:
            user_flags[k] = v
            
    store[str(erp_id)] = user_flags
    _write_store(store)
    return user_flags
