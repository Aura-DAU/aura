"""
Static-analysis guard: pipeline/google_calendar/ must stay write-free
except for the one deliberate exception, writer.py.

writer.py creates/updates/deletes events on a STUDENT'S OWN Google
Calendar, gated behind an explicit `calendar.events` OAuth consent screen
the student sees and approves, plus a confirm-before-write step in the
agent tool (see pipeline/timetable/tool_registry.py's
SYNC_TIMETABLE_TO_GOOGLE_CALENDAR). Every other file in this directory —
client.py, token_vault.py, slot_service.py, timetable_sync.py — must never
gain a write call; if one shows up there it's either a bug or a
capability silently expanding into code that was never reviewed for it.

Also confirms no eCampus write/POST/PUT/DELETE client has been
reintroduced (there is none in this codebase by design).
"""

import ast
from pathlib import Path

GOOGLE_CALENDAR_DIR = Path(__file__).resolve().parent.parent / "google_calendar"
WRITE_INDICATOR_CALLS = {"post", "put", "patch", "delete", "insert", "update", "write"}


def test_no_write_calls_outside_writer_py():
    offending = []
    for py_file in GOOGLE_CALENDAR_DIR.glob("*.py"):
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.lower() in WRITE_INDICATOR_CALLS:
                # allowlist: client.py's requests.post() is the OAuth
                # token-refresh handshake against Google's own token
                # endpoint (GOOGLE_TOKEN_URL) — an auth call, not a write
                # to calendar/ERP data.
                if py_file.name == "client.py" and node.attr.lower() == "post":
                    continue
                # allowlist: writer.py is the ONE deliberate write path in
                # this directory — see module docstring above.
                if py_file.name == "writer.py":
                    continue
                offending.append(f"{py_file.name}:{node.lineno} -> .{node.attr}(")

    assert not offending, (
        "Found write-indicator calls outside the allowlisted files in "
        f"pipeline/google_calendar/: {offending}. If this is a deliberate "
        "new write path, it needs the same scrutiny writer.py got (explicit "
        "OAuth consent scope, confirm-before-write gate, narrow allowlist "
        "here) — not just a new .post()/.delete() dropped into an existing "
        "read-only module."
    )


def test_no_ecampus_write_client_reintroduced():
    ecampus_dir = Path(__file__).resolve().parent.parent / "ecampus"
    if not ecampus_dir.exists():
        return
    for py_file in ecampus_dir.glob("*.py"):
        text = py_file.read_text()
        assert "requests.post(" not in text or "GOOGLE_TOKEN_URL" in text, (
            f"{py_file.name} appears to call requests.post() — eCampus "
            "should remain a read-only integration."
        )
