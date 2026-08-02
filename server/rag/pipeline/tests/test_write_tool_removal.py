# v7 regression: write-tool + attendance-tool removal.
#
# AURA started life as a strictly read-only assistant. That invariant has since
# gained a small number of deliberate, product-approved exceptions. Rather than
# deleting the invariant (which would let accidental writes back in) or leaving
# the tests red, each known write path is recorded as an explicit carve-out in
# the allowlists below, with the PR/commit that introduced it and why.
#
# Rules for the allowlists:
#   * Adding an entry is a product decision — it belongs in a PR that explains
#     the write path, not a drive-by "make CI green" commit.
#   * Entries are asserted to still be live. If a carve-out's write path is
#     removed, the corresponding test fails so the stale exception gets deleted
#     instead of silently re-opening a hole for a future write.

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.ecampus.tool_registry import TOOL_REGISTRY

REMOVED_TOOL_NAMES = {
    "refresh_my_data",
    "share_data_with_advisor",
    "revoke_advisor_access",
    "get_attendance",
    "check_exam_eligibility",
}

WRITE_INDICATOR_CALLS = {
    "post", "put", "patch", "delete",  # requests.post / .put / .patch / .delete
    "insert", "update", "write",       # generic write-ish method names
}

# Tools that are allowed to carry category="write". Name -> why.
ALLOWED_WRITE_TOOLS = {
    "update_tracking_flags": (
        "Persists personal profile facts the user volunteered in conversation "
        "(DOB, age, interests) to AURA's own tracking store. Writes only to "
        "AURA-owned storage for the calling user — never to the ERP, and "
        "never to another user's data. Added in 0011a0a (#247)."
    ),
}

# Modules under pipeline/ecampus/ and pipeline/google_calendar/ allowed to
# contain write-indicator call sites, narrowed to the specific method names
# each one legitimately needs. A method not listed here still fails the guard,
# so e.g. a new requests.delete() in session.py would be caught.
ALLOWED_HTTP_WRITE_MODULES = {
    "session.py": {
        "methods": {"update", "post"},
        "reason": (
            "The eCampus scraping session client. `.update()` is dict "
            "mutation on the request headers, and `.post()` submits the ERP "
            "login form and subsequent ASP.NET postbacks — the only way to "
            "read a page behind that form. No ERP record is created."
        ),
    },
    "client.py": {
        "methods": {"post"},
        "reason": (
            "The Google OAuth token-refresh handshake against Google's own "
            "token endpoint (GOOGLE_TOKEN_URL). An auth call, not a write."
        ),
    },
    "writer.py": {
        "methods": {"post", "delete"},
        "reason": (
            "Google Calendar timetable sync — the one module in AURA that "
            "writes calendar events, by design. Touches only events it "
            "created itself (tagged extendedProperties.private.aura_slot_key) "
            "on the calendar of the erp_id that granted the calendar.events "
            "scope. Updates are encoded inside its batch POST; stale and "
            "unsynced AURA-managed events use direct DELETE requests. Added "
            "in 893130f (#195); see the module docstring."
        ),
    },
    "revoke.py": {
        "methods": {"post"},
        "reason": (
            "Best-effort Google OAuth revocation during calendar disconnect. "
            "The POST targets Google's revocation endpoint before AURA deletes "
            "the calling user's locally stored token. Added in a206b1cd (#303)."
        ),
    },
    "retry_queue.py": {
        "methods": {"post"},
        "reason": (
            "Retries a failed Google Calendar event creation for the same "
            "authenticated user and slot previously approved for timetable "
            "sync. Added in a206b1cd (#303)."
        ),
    },
}

GUARDED_DIRS = ("ecampus", "google_calendar")


def _write_indicator_call_sites() -> list[tuple[str, int, str]]:
    """Static-analysis scan of the guarded packages. Returns every call site
    whose attribute name looks like a write, as (filename, lineno, attr)."""
    pipeline_dir = Path(__file__).resolve().parent.parent
    sites = []
    for dirname in GUARDED_DIRS:
        for py_file in (pipeline_dir / dirname).glob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute):
                    continue
                attr = node.attr.lower()
                if attr in WRITE_INDICATOR_CALLS:
                    sites.append((py_file.name, node.lineno, attr))
    return sites


def test_removed_tools_absent_from_registry():
    for name in REMOVED_TOOL_NAMES:
        assert name not in TOOL_REGISTRY, f"{name} should have been removed from TOOL_REGISTRY"


def test_no_undocumented_write_category_tools():
    for tool in TOOL_REGISTRY.values():
        if tool.category in ("read", "derived"):
            continue
        assert tool.category == "write", (
            f"{tool.name} has unexpected category={tool.category!r} — "
            "tools must be 'read', 'derived', or an allowlisted 'write'"
        )
        assert tool.name in ALLOWED_WRITE_TOOLS, (
            f"{tool.name} has category='write' but is not in "
            "ALLOWED_WRITE_TOOLS. AURA is read-only by default; a new write "
            "tool needs an explicit, reviewed carve-out in this test "
            "explaining what it writes and why."
        )


def test_allowed_write_tools_are_not_stale():
    # If a carve-out's tool is gone (or is no longer a write), delete the entry
    # rather than leaving a standing exception a future write could slip into.
    for name in ALLOWED_WRITE_TOOLS:
        assert name in TOOL_REGISTRY, (
            f"{name} is allowlisted in ALLOWED_WRITE_TOOLS but no longer "
            "exists in TOOL_REGISTRY — remove the stale carve-out"
        )
        assert TOOL_REGISTRY[name].category == "write", (
            f"{name} is allowlisted in ALLOWED_WRITE_TOOLS but its category "
            f"is {TOOL_REGISTRY[name].category!r} — remove the stale carve-out"
        )


def _allowed_methods(filename: str) -> set:
    return ALLOWED_HTTP_WRITE_MODULES.get(filename, {}).get("methods", set())


def test_ecampus_package_has_no_undocumented_http_write_calls():
    offending = [
        f"{filename}:{lineno} -> .{attr}("
        for filename, lineno, attr in _write_indicator_call_sites()
        if attr not in _allowed_methods(filename)
    ]
    assert not offending, (
        f"Found undocumented write call sites: {offending}. If one of these "
        "is intentional, add it to ALLOWED_HTTP_WRITE_MODULES with the PR "
        "that introduced it and why it is safe."
    )


def test_allowed_http_write_modules_are_not_stale():
    # Every allowlisted (module, method) pair must still have a live call site,
    # so removing a write path also removes its exception.
    pipeline_dir = Path(__file__).resolve().parent.parent
    sites = _write_indicator_call_sites()

    for filename, carve_out in ALLOWED_HTTP_WRITE_MODULES.items():
        exists = any(
            (pipeline_dir / d / filename).exists() for d in GUARDED_DIRS
        )
        assert exists, (
            f"{filename} is allowlisted in ALLOWED_HTTP_WRITE_MODULES but no "
            "longer exists — remove the stale carve-out"
        )
        for method in carve_out["methods"]:
            assert any(f == filename and a == method for f, _, a in sites), (
                f"{filename} is allowlisted for .{method}() but no such call "
                "site remains — remove the stale carve-out"
            )
