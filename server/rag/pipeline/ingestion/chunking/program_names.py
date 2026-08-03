"""
Canonical programme-name normalization for ingestion.

Retrieval filters (retrieval_pipeline.PROGRAM_ALIASES) are expressed against
canonical programme names like "B.Tech. (ICT)" / "M.Sc. (IT)" / "Ph.D.".
Ingestion previously wrote whatever raw string the body-text regex or the
page title produced ('B Tech', 'MTech ICT', 'Ph D', stray OCR sentences...),
so programme metadata filters matched zero chunks in both BM25 and Qdrant.

Every value written into a chunk's `program_name` MUST pass through
canonicalize_program_value() so the corpus only ever contains the canonical
spellings retrieval queries with. Unrecognized values are dropped (returning
None) rather than stored: a junk programme name is worse than none, because
it can never match a filter but still pollutes the entity index.

The normalization transform below (lowercase, strip punctuation, collapse
"b tech" -> "btech", ...) is intentionally identical to
RetrievalPipeline._normalize_program_name so both sides agree on keys.
"""

import re

ICT_CS_PROGRAM_NAME = "B.Tech. (Honours) in ICT with minor in Computational Science"

# Keys are POST-normalization strings (see _normalize_key). Values are the
# canonical programme names used by retrieval-side filters.
CANONICAL_PROGRAM_ALIASES = {
    # Broad programme sentinels (document mentions the degree without a
    # specialization — kept so "M.Tech fee" style filters still match).
    "btech": "B.Tech.",
    "mtech": "M.Tech.",
    "msc": "M.Sc.",
    "mdes": "M.Des.",
    "phd": "Ph.D.",
    "doctoral": "Ph.D.",

    # B.Tech specializations
    "btech ict": "B.Tech. (ICT)",
    "ict": "B.Tech. (ICT)",
    "btech ict cs": ICT_CS_PROGRAM_NAME,
    "btech ictcs": ICT_CS_PROGRAM_NAME,
    "btech honours ict": ICT_CS_PROGRAM_NAME,
    "btech honours in ict": ICT_CS_PROGRAM_NAME,
    "btech honours in ict with minor in computational science": ICT_CS_PROGRAM_NAME,
    "btech csai": "B.Tech. (CS and AI)",
    "btech cs ai": "B.Tech. (CS and AI)",
    "btech cs and ai": "B.Tech. (CS and AI)",
    "computer science and artificial intelligence": "B.Tech. (CS and AI)",
    "btech ece": "B.Tech. (ECE-AI)",
    "btech ece ai": "B.Tech. (ECE-AI)",
    "electronics and communication": "B.Tech. (ECE-AI)",
    "btech evd": "B.Tech. (EVD)",
    "btech mnc": "B.Tech. (MnC)",
    "mathematics and computing": "B.Tech. (MnC)",

    # M.Tech
    "mtech ict": "M.Tech. (ICT)",
    "mtech ec": "M.Tech. (EC)",
    "mtech ece": "M.Tech. (EC)",
    "mtech cs and ml": "M.Tech. (CS and ML)",
    "mtech cs ml": "M.Tech. (CS and ML)",

    # M.Sc.
    "msc it": "M.Sc. (IT)",
    "mscit": "M.Sc. (IT)",
    "msc information technology": "M.Sc. (IT)",
    "msc ds": "M.Sc. (Data Science)",
    "msc data science": "M.Sc. (Data Science)",
    "msc aa": "M.Sc. (Agriculture Analytics)",
    "msc agriculture analytics": "M.Sc. (Agriculture Analytics)",

    # M.Des.
    "mdes cd": "M.Des. (CD)",
    "mdes iuxd": "M.Des. (IUxD)",

    # BS-MS dual degree
    "bs ms": "BS-MS (Data Science & Artificial Intelligence)",
    "bs ms dsai": "BS-MS (Data Science & Artificial Intelligence)",
    "bs ms ds ai": "BS-MS (Data Science & Artificial Intelligence)",
    "bs ms data science": "BS-MS (Data Science & Artificial Intelligence)",
    "bs ms data science artificial intelligence": "BS-MS (Data Science & Artificial Intelligence)",
    "bs ms it": "BS-MS (Information Technology)",
    "bs ms information technology": "BS-MS (Information Technology)",
}


def _normalize_key(name):
    """Mirror of RetrievalPipeline._normalize_program_name — keep in sync."""
    name = str(name).lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.replace("b tech", "btech")
    name = name.replace("m tech", "mtech")
    name = name.replace("m des", "mdes")
    name = name.replace("m sc", "msc")
    name = re.sub(r"\bph\s*d\b", "phd", name)
    return name


def canonicalize_program_name(raw):
    """Map one raw programme mention to its canonical name, or None."""
    if raw is None:
        return None
    key = _normalize_key(raw)
    if not key:
        return None
    return CANONICAL_PROGRAM_ALIASES.get(key)


def canonicalize_program_value(value):
    """Canonicalize a scalar or list program_name metadata value.

    Returns a canonical string, a sorted deduped list of canonical strings,
    or None when nothing recognizable remains.
    """
    if value is None:
        return None
    items = value if isinstance(value, list) else [value]
    canonical = sorted({c for c in (canonicalize_program_name(v) for v in items) if c})
    if not canonical:
        return None
    return canonical[0] if len(canonical) == 1 else canonical
