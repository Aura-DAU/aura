"""
Logs every personal-data access attempt — allowed or denied. Swap the flat
file for a real log sink (CloudWatch, ELK, whatever DAU already runs) before
production; this still beats having no record at all.
"""

import json
import time
import os

AUDIT_LOG_PATH = os.environ.get("AURA_AUDIT_LOG", "/var/log/aura/personal_data_audit.log")


def audit_log(identity: dict, query: str, allowed: bool, target: str | None = None, reason: str | None = None) -> None:
    entry = {
        "ts": time.time(),
        "requester_role": (identity or {}).get("role"),
        "requester_id": (identity or {}).get("erp_id"),
        "query": query,
        "allowed": allowed,
        "target_student_id": target,
        "reason": reason,
    }
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
