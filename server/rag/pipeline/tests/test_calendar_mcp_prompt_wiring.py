from pathlib import Path

from pipeline.prompt_loader import load_calendar_mcp_system_prompt


RAG_DIR = Path(__file__).resolve().parents[2]
PROMPT_PATH = RAG_DIR / "p&q" / "calendar_mcp_system_prompt.md"
ORCHESTRATOR_PATH = RAG_DIR / "pipeline" / "ecampus" / "orchestrator.py"
MCP_SERVER_PATH = RAG_DIR / "mcp_servers" / "gcal_server.py"


def test_calendar_mcp_prompt_is_loaded_by_the_orchestrator():
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    orchestrator = ORCHESTRATOR_PATH.read_text(encoding="utf-8")
    mcp_server = MCP_SERVER_PATH.read_text(encoding="utf-8")

    assert load_calendar_mcp_system_prompt() == prompt.strip()
    assert "preview_timetable_sync" in prompt
    assert "sync_timetable_to_calendar" in prompt
    assert "CALENDAR_MCP_SYSTEM_PROMPT" in orchestrator
    assert "load_calendar_mcp_system_prompt" in orchestrator
    assert "instructions=load_calendar_mcp_system_prompt()" in mcp_server


def test_calendar_mcp_prompt_overrides_generic_personal_data_refusals():
    prompt = load_calendar_mcp_system_prompt()
    normalized_prompt = " ".join(prompt.split())

    assert "take precedence over generic rules about personal data" in normalized_prompt
    assert '"sync my Google Calendar"' in normalized_prompt
    assert "call `sync_timetable_to_calendar` immediately" in normalized_prompt
    assert "do not ask for section, electives, or another confirmation" in normalized_prompt
    assert "Google Calendar only, not Google Classroom" in normalized_prompt
    assert "Never answer a supported request with a generic refusal" in normalized_prompt
