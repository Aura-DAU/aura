from __future__ import annotations
import os
import re
import json
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "institution_aliases.json"


class InstitutionResolver:
    """
    Institution Context Resolver Middleware.
    Executes BEFORE the Query Planner and Vector Search.
    
    Responsibilities:
    - Resolves institutional abbreviations, acronyms, and synonyms (e.g. DADC -> Dance Club (DADC) at DAU).
    - Uses a maintainable JSON/YAML alias registry rather than hardcoding in LLM prompts.
    - Supports exact token matching and fuzzy matching for minor typos.
    - Low-latency (<1ms), fully deterministic pre-processing.
    """

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.aliases: List[Dict[str, Any]] = []
        self.abbrev_map: Dict[str, Dict[str, Any]] = {}
        self.synonym_map: Dict[str, Dict[str, Any]] = {}
        self.patterns: List[Tuple[re.Pattern, Dict[str, Any]]] = []
        self._load_registry()

    def _load_registry(self) -> None:
        """Load and index the institutional alias registry."""
        if not self.config_path.exists():
            # Fallback inline defaults if config file is missing
            self.aliases = [
                {
                    "canonical_name": "Dance Club (DADC)",
                    "abbreviation": "DADC",
                    "synonyms": ["Dance Club", "DADC Club"],
                    "category": "Club"
                },
                {
                    "canonical_name": "Artificial Intelligence Club (AI Club)",
                    "abbreviation": "AI Club",
                    "synonyms": ["AI Club", "Artificial Intelligence Club"],
                    "category": "Club"
                },
                {
                    "canonical_name": "Career Development Cell (CDC)",
                    "abbreviation": "CDC",
                    "synonyms": ["CDC", "Placement Cell", "Career Development Cell"],
                    "category": "Department"
                },
                {
                    "canonical_name": "Student Affairs Council (SAC)",
                    "abbreviation": "SAC",
                    "synonyms": ["SAC", "Student Affairs Council"],
                    "category": "Administrative Body"
                },
                {
                    "canonical_name": "University Hostel Office",
                    "abbreviation": "Hostel Office",
                    "synonyms": ["Hostel Office", "Hostel Warden Office"],
                    "category": "Facility"
                },
                {
                    "canonical_name": "University Dining Services (Mess)",
                    "abbreviation": "Mess",
                    "synonyms": ["Mess", "Dining Hall", "Canteen", "Student Mess"],
                    "category": "Facility"
                },
                {
                    "canonical_name": "University ERP Portal",
                    "abbreviation": "ERP",
                    "synonyms": ["ERP", "ERP Portal", "Academic Portal"],
                    "category": "System"
                }
            ]
        else:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.aliases = data.get("aliases", [])

        self.abbrev_map = {}
        self.synonym_map = {}
        self.patterns = []

        for entity in self.aliases:
            abbrev = entity.get("abbreviation")
            if abbrev:
                self.abbrev_map[abbrev.upper()] = entity

            for syn in entity.get("synonyms", []):
                self.synonym_map[syn.lower()] = entity

            # Build regex patterns for exact word boundaries
            all_terms = set()
            if abbrev:
                all_terms.add(re.escape(abbrev))
            for syn in entity.get("synonyms", []):
                all_terms.add(re.escape(syn))

            # Compile regex pattern sorting by length descending to match longest phrases first
            sorted_terms = sorted(all_terms, key=len, reverse=True)
            pattern_str = r"\b(?:" + "|".join(sorted_terms) + r")\b"
            compiled = re.compile(pattern_str, re.IGNORECASE)
            self.patterns.append((compiled, entity))

    def expansions(self, query: str) -> List[str]:
        """Canonical names of the institutional entities the query mentions,
        excluding any whose canonical name the query already contains."""
        if not query:
            return []

        query_lower = query.lower()
        found: List[str] = []

        for compiled_pat, entity in self.patterns:
            canonical = entity.get("canonical_name", "")
            if canonical and compiled_pat.search(query) and canonical not in found:
                found.append(canonical)

        # Fuzzy fallback for typos in abbreviations ("DADCC"), only when no
        # exact alias matched.
        if not found:
            for word in query.split():
                clean_word = re.sub(r"[^\w]", "", word).upper()
                if len(clean_word) < 3:
                    continue
                for abbrev, entity in self.abbrev_map.items():
                    if difflib.SequenceMatcher(None, clean_word, abbrev).ratio() >= 0.85:
                        canonical = entity.get("canonical_name", "")
                        if canonical and canonical not in found:
                            found.append(canonical)
                        break

        return [c for c in found if c.lower() not in query_lower]

    def resolve(self, query: str) -> str:
        """
        Append the canonical names of institutional abbreviations and synonyms
        as a retrieval hint, leaving the user's own words untouched.
        Example: "Who is the convenor of DADC?" ->
        "Who is the convenor of DADC? (Dance Club (DADC))"

        Idempotent: resolving an already-resolved query returns it unchanged,
        because canonical names already present are not appended again.
        """
        extra = self.expansions(query)
        if not extra:
            return query
        return f"{query} ({'; '.join(extra)})"

    def get_entity_info(self, term: str) -> Optional[Dict[str, Any]]:
        """Look up institutional entity info by abbreviation or synonym."""
        if not term:
            return None
        term_upper = term.strip().upper()
        if term_upper in self.abbrev_map:
            return self.abbrev_map[term_upper]
        
        term_lower = term.strip().lower()
        if term_lower in self.synonym_map:
            return self.synonym_map[term_lower]

        return None


# Global singleton instance for high-performance zero-cost reuse
_resolver_instance: Optional[InstitutionResolver] = None

def get_institution_resolver() -> InstitutionResolver:
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = InstitutionResolver()
    return _resolver_instance
