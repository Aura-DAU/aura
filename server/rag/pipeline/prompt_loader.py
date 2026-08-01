from functools import lru_cache
from pathlib import Path


_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "p&q"


@lru_cache(maxsize=1)
def load_calendar_mcp_system_prompt() -> str:
    prompt_path = _PROMPTS_DIR / "calendar_mcp_system_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise RuntimeError(f"Calendar MCP system prompt is empty: {prompt_path}")
    return prompt
