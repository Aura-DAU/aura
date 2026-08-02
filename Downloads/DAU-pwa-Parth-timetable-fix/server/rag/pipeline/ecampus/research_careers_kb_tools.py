"""
Research / placements / careers KB skills — read-only.

KB sources (primary):
  research — data/research/ (areas, labs, publications, IRB, awards)
  placements / careers — data/placements/, data/careers/

Does NOT replace faculty workflow tools:
  seed_grant_guidance, cpda_travel_approval_guidance — keep using those for
  personal faculty process checklists. This module answers general research /
  placement KB questions.
"""

from .kb_retrieval import (
    PUBLIC_READER_ROLES,
    audit,
    require_role,
    run_kb_query,
)

_RESEARCH_PROMPT = """
You are AURA's research information assistant. Using ONLY the retrieved
research context, summarize research areas, labs, publications, IRB, awards,
or related research policies asked about.
Rules:
- Never invent lab names, awards, or policy clauses.
- For personal faculty seed-grant / CPDA process checklists, note that
  seed_grant_guidance / cpda_travel_approval_guidance are the right tools.
- Mark missing details as "Not specified in the retrieved documents".
"""

_PLACEMENT_PROMPT = """
You are AURA's placements / careers assistant. Using ONLY the retrieved
placement-cell / careers context, summarize process steps, policies,
statistics, brochure facts, or company categorization rules asked about.
Rules:
- Never invent placement statistics, company lists, or policy exceptions.
- Prefer the most recent year when multiple years appear; name the year used.
- AURA cannot register a student for placements — remind them to use the
  official Placement Cell channel when action is needed.
"""


def handle_lookup_research_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Research areas, labs, publications, IRB, research policies from data/research/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up research information.",
    )
    topic = (topic or kwargs.get("query") or kwargs.get("research_area") or "").strip()
    if topic:
        query = (
            f"{topic} research area laboratory publications IRB seed grant "
            f"faculty research accomplishments outreach"
        )
        user_message = f"Research information about: {topic}"
    else:
        query = "research areas laboratories publications overview DAU DA-IICT"
        user_message = "Summarize research areas / labs covered in the knowledge base."
    out = run_kb_query(
        query, "student", _RESEARCH_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching research information in the knowledge base.",
    )
    audit(identity, "lookup_research_info", topic or "overview")
    return out


def handle_lookup_placement_careers_info(identity, topic: str = "", request_context=None, **kwargs) -> dict:
    """Placement process, policies, and careers info from data/placements/ + careers/."""
    require_role(
        identity, PUBLIC_READER_ROLES,
        "This tool is for students and faculty looking up placements/careers information.",
    )
    topic = (topic or kwargs.get("query") or "").strip()
    if topic:
        query = (
            f"{topic} placement process policy statistics brochure career "
            f"company categorization offer rejection dream category IPRS"
        )
        user_message = f"Placements / careers question: {topic}"
    else:
        query = (
            "placement cell process steps statistics brochure company "
            "categorization offer policy overview"
        )
        user_message = "Summarize placement process / careers information available."
    out = run_kb_query(
        query, "student", _PLACEMENT_PROMPT, user_message,
        request_context=request_context,
        empty_response="I couldn't find matching placements/careers information in the knowledge base.",
    )
    audit(identity, "lookup_placement_careers_info", topic or "overview")
    return out
