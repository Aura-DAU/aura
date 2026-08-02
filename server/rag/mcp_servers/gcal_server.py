#Google Calendar MCP server for AURA.
import sys
from pathlib import Path

# The app splits its import roots across two dirs: `pipeline` /
# `personal_query_classifier` live under server/rag, while `db` / `api` live
# under server. Put BOTH on sys.path so the server runs from whatever CWD the
# MCP host launches it from. (This mirrors what the test conftest does.)
# Deliberately NOT placed in a package named ``mcp`` -- that would shadow the
# installed ``mcp`` SDK.
_RAG_ROOT = Path(__file__).resolve().parents[1]     # .../server/rag
_SERVER_ROOT = Path(__file__).resolve().parents[2]  # .../server
for _root in (_RAG_ROOT, _SERVER_ROOT):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from mcp.server import MCPServer  # noqa: E402  (after sys.path bootstrap)

from pipeline.google_calendar import timetable_sync  # noqa: E402
from pipeline.prompt_loader import load_calendar_mcp_system_prompt  # noqa: E402

mcp = MCPServer(
    name="aura-google-calendar",
    version="0.1.0",
    instructions=load_calendar_mcp_system_prompt(),
)


def _identity(erp_id: str) -> dict:
    """Minimal identity the timetable/calendar services accept. Cohort
    (year/sem/sec) is resolved downstream from user_identity_map by erp_id."""
    return {"role": "student", "erp_id": erp_id}


@mcp.tool()
def calendar_status(erp_id: str) -> dict:
    """Report whether this student has connected Google Calendar with write
    access. Returns {"calendar_linked": bool}."""
    return timetable_sync.status(_identity(erp_id))


@mcp.tool()
def preview_timetable_sync(erp_id: str) -> dict:
    """Dry run: show how many class events WOULD be created/updated on the
    student's Google Calendar, without writing anything. Call this first and
    relay the count to the user before syncing."""
    res = timetable_sync.preview(_identity(erp_id))
    print("DEBUG GCAL SERVER preview_timetable_sync RES:", res)
    return res


@mcp.tool()
def sync_timetable_to_calendar(erp_id: str) -> dict:
    """Create/update recurring weekly events for every class on the student's
    current AURA timetable -- with popup reminders, running until the end of
    the semester. Only call after preview_timetable_sync and explicit user
    confirmation. Returns status 'synced' with created/updated/removed counts,
    or 'calendar_not_connected' if the student hasn't linked write access."""
    return timetable_sync.apply(_identity(erp_id))


@mcp.tool()
def unsync_timetable_from_calendar(erp_id: str) -> dict:
    """Remove every timetable event AURA previously created on the student's
    Google Calendar. Returns status 'unsynced' with the count removed."""
    return timetable_sync.unsync(_identity(erp_id))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
