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

    def resolve(self, query: str) -> str:
        """
        Resolve institutional abbreviations and synonyms in the query text.
        Example: "Who is the convenor of DADC?" -> "Who is the convenor of Dance Club (DADC) at DAU?"
        Returns the enhanced internal query string for Query Planner & Retriever.
        """
        if not query:
            return query

        resolved_query = query
        matched_entities = set()

        # Step 1: Exact Regex Match & Expansion
        for compiled_pat, entity in self.patterns:
            canonical = entity.get("canonical_name", "")
            abbrev = entity.get("abbreviation", "")
            replacement = f"{canonical} at DAU" if "at DAU" not in canonical else canonical

            def _replace_match(m):
                matched_entities.add(canonical)
                return replacement

            # Perform replacement if pattern matches
            if compiled_pat.search(resolved_query):
                resolved_query = compiled_pat.sub(_replace_match, resolved_query)

        # Step 2: Fuzzy Matching Fallback (if no regex patterns matched)
        if not matched_entities:
            words = query.split()
            for word in words:
                clean_word = re.sub(r"[^\w]", "", word).upper()
                if len(clean_word) >= 3:
                    for abbrev, entity in self.abbrev_map.items():
                        ratio = difflib.SequenceMatcher(None, clean_word, abbrev).ratio()
                        if ratio >= 0.85: # High confidence fuzzy match
                            canonical = entity.get("canonical_name", "")
                            replacement = f"{canonical} at DAU"
                            resolved_query = re.sub(r"\b" + re.escape(word) + r"\b", replacement, resolved_query, flags=re.IGNORECASE)
                            break

        return resolved_query

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
