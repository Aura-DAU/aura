# v7 regression: write-tool + attendance-tool removal.
# Confirms TOOL_REGISTRY never re-exports refresh_my_data,
# this test guards against one being reintroduced).

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


def test_removed_tools_absent_from_registry():
    for name in REMOVED_TOOL_NAMES:
        assert name not in TOOL_REGISTRY, f"{name} should have been removed from TOOL_REGISTRY"


def test_no_write_category_tools_remain():
    for tool in TOOL_REGISTRY.values():
        assert tool.category in ("read", "derived"), (
            f"{tool.name} has category={tool.category!r} — "
            "AURA is read-only, no 'write' category should exist"
        )


def test_ecampus_package_has_no_http_write_calls():
    # Static-analysis guard: walk every .py file under pipeline/ecampus/ and
    # pipeline/google_calendar/ and fail if any call site looks like an HTTP
    # substitute for code review.
    ecampus_dir = Path(__file__).resolve().parent.parent / "ecampus"
    calendar_dir = Path(__file__).resolve().parent.parent / "google_calendar"

    offending = []
    for directory in (ecampus_dir, calendar_dir):
        for py_file in directory.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr.lower() in WRITE_INDICATOR_CALLS:
                    # allowlist: reminder_tool.py's build_reminder_link only
                    # builds a URL string, never calls requests.post/etc.
                    if py_file.name == "reminder_tool.py":
                        continue
                    # allowlist: session.py is the scraping session client which
                    # performs logins and form-submissions (ASP.NET postbacks).
                    if py_file.name == "session.py":
                        continue
                    # allowlist: client.py's requests.post() is the OAuth
                    # token-refresh handshake against Google's own token
                    # endpoint (GOOGLE_TOKEN_URL) — an auth call, not a write
                    # to calendar/ERP data. The calendar scope requested is
                    # calendar.readonly (see client.py's own docstring).
                    if py_file.name == "client.py" and node.attr.lower() == "post":
                        continue
                    offending.append(f"{py_file.name}:{node.lineno} -> .{node.attr}(")

    assert not offending, f"Found possible write call sites: {offending}"
