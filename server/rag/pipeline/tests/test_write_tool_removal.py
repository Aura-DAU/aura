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
from pathlib import Path

WRITE_INDICATOR_CALLS = {
    "post", "put", "patch", "delete",  # requests.post / .put / .patch / .delete
    "insert", "update", "write",       # generic write-ish method names
}

# Modules under pipeline/google_calendar/ allowed to
# contain write-indicator call sites, narrowed to the specific method names
# each one legitimately needs. A method not listed here still fails the guard,
# so e.g. a new requests.delete() in client.py would be caught.
ALLOWED_HTTP_WRITE_MODULES = {
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

GUARDED_DIRS = ("google_calendar",)


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


def _allowed_methods(filename: str) -> set:
    return ALLOWED_HTTP_WRITE_MODULES.get(filename, {}).get("methods", set())


def test_google_calendar_package_has_no_undocumented_http_write_calls():
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
