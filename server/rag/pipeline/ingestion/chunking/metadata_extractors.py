import re

# Academic-year labels like "2024-25", "24-25", "2026_27". Used so scraped_date
# (ingest timestamp) never masquerades as the roster/policy year — that bug made
# "Club Committee Data 24-25" surface as rule_year=2026 and beat newer C_DCs sheets.
_ACADEMIC_YEAR_RE = re.compile(
    r"(?:(?P<y4>20\d{2})|(?<!\d)(?P<y2>\d{2}))[_\-\u2013](?P<yend>\d{2})(?!\d)"
)


def normalize_academic_year_label(text: str | None) -> str | None:
    """Return a canonical 'YYYY-YY' academic year from free text, or None.

    Rejects non-academic ranges (e.g. room codes like '12-34') by requiring
    the end year to be start+1.
    """
    if not text:
        return None
    match = _ACADEMIC_YEAR_RE.search(str(text))
    if not match:
        return None
    start = int(match.group("y4") or f"20{match.group('y2')}")
    end_raw = match.group("yend")
    end = int(end_raw) if len(end_raw) == 4 else (start // 100) * 100 + int(end_raw)
    # Two-digit end years wrap the century boundary (e.g. 1999-00).
    if end < start:
        end += 100
    if end != start + 1:
        return None
    # Bound to plausible DAU academic years; rejects room/time ranges like 10-11.
    if start < 2015 or start > 2035:
        return None
    return f"{start}-{end % 100:02d}"


def academic_year_start(label: str | None) -> int | None:
    """Sort key: start calendar year of a 'YYYY-YY' label."""
    if not label:
        return None
    match = re.match(r"^(20\d{2})-\d{2}$", str(label).strip())
    return int(match.group(1)) if match else None


def resolve_document_academic_year(metadata: dict, file_path, body: str = "") -> tuple:
    """Pick the authoritative academic year for a corpus file.

    Preference order (title/filename beat scraped_date on purpose):
      1. Explicit frontmatter academic label (document_year/year/academic_year
         when it parses as YYYY-YY)
      2. Academic-year pattern in title, original_name, or filename
      3. Bare 20xx calendar year in title / filename / path / body head
      4. Bare numeric frontmatter year (last among calendar-year sources)
      5. scraped_date year (ingest time — last resort only)
      6. Today's calendar year

    Returns (document_year:int, academic_year:str|None).
    """
    import datetime
    from pathlib import Path

    path = Path(file_path) if not isinstance(file_path, Path) else file_path
    title = str(metadata.get("title") or "")
    original_name = str(metadata.get("original_name") or "")
    path_name = path.name
    path_str = str(path)

    # 1. Explicit academic *label* in frontmatter only (not bare ints — those
    # often come from scraped_date backfills and must lose to title years).
    for key in ("academic_year", "document_year", "year"):
        raw = metadata.get(key)
        if raw is None:
            continue
        label = normalize_academic_year_label(str(raw))
        if label:
            return academic_year_start(label) or int(label[:4]), label

    # 2. Title / filename academic labels beat bare calendar years.
    for candidate in (title, original_name, path_name, path_str):
        label = normalize_academic_year_label(candidate)
        if label:
            return academic_year_start(label) or int(label[:4]), label

    # 3. Bare 20xx in title/path/body.
    for candidate in (title, path_name, path_str, (body or "")[:1000]):
        year_match = re.search(r"\b(20\d{2})\b", str(candidate))
        if year_match:
            return int(year_match.group(1)), None

    # 4. Bare numeric frontmatter year (after title/path opportunities).
    for key in ("document_year", "year"):
        raw = metadata.get(key)
        if raw is None:
            continue
        try:
            year_int = int(str(raw).strip()[:4])
            if 2000 <= year_int <= 2100:
                return year_int, None
        except (TypeError, ValueError):
            pass

    scraped = metadata.get("scraped_date")
    if scraped is not None:
        year_match = re.search(r"\b(20\d{2})\b", str(scraped))
        if year_match:
            return int(year_match.group(1)), None

    return datetime.date.today().year, None


def extract_academic_applicability(metadata, file_path, body):
    """Deterministically classify document applicability for student scope.

    Academic policy documents without a confident programme and admission range
    remain unclassified; they are intentionally excluded from scoped retrieval.
    """
    # Explicit, reviewed frontmatter is authoritative. This lets the content
    # owner safely tag exceptions that cannot be inferred from a filename or
    # policy title, while keeping the ingestion output deterministic.
    explicit_scope = metadata.get("applicability_scope")
    if explicit_scope:
        result = {"applicability_scope": str(explicit_scope)}
        for key in (
            "programme_id",
            "branch_id",
            "department_id",
            "degree_level",
            "course_code",
            "curriculum_version",
            "regulation_version",
        ):
            if metadata.get(key) is not None:
                result[key] = str(metadata[key])
        for key in ("admission_year_from", "admission_year_to"):
            if metadata.get(key) is not None:
                try:
                    result[key] = int(metadata[key])
                except (TypeError, ValueError):
                    # Invalid reviewed metadata must fail closed at retrieval.
                    result[key] = None
        return result

    category = str(metadata.get("category") or "").lower()
    path_text = str(file_path).replace("\\", "/").lower()
    title = str(metadata.get("title") or "")
    haystack = " ".join([title, path_text, body[:4000]]).lower()
    academic = "academics" in path_text or "academic" in category
    if not academic:
        return {"applicability_scope": "global"}

    programme_patterns = [
        (r"b\.?\s*tech\s*\(?\s*ict\s*\)?", "btech-ict", "undergraduate"),
        (r"(?:b\.?\s*tech\s*\(?\s*mnc|mathematics and computing)", "btech-mnc", "undergraduate"),
        (r"(?:b\.?\s*tech\s*\(?\s*evd|electronics and vlsi)", "btech-evd", "undergraduate"),
        (r"(?:m\.?\s*sc\s*\(?\s*ds|m\.sc.*data science)", "msc-ds", "postgraduate"),
        (r"(?:m\.?\s*sc\s*\(?\s*it|m\.sc.*information technology)", "msc-it", "postgraduate"),
        (r"m\.?\s*tech\s*\(?\s*ict", "mtech-ict", "postgraduate"),
        (r"m\.?\s*tech\s*\(?\s*ec", "mtech-ec", "postgraduate"),
        (r"ph\.?\s*d", "phd", "doctoral"),
    ]
    programme = next(((pid, level) for pattern, pid, level in programme_patterns if re.search(pattern, haystack)), None)
    admitted = re.search(r"(?:admitted|admission)\D{0,40}(20\d{2})(?:\s*[-–/]\s*\d{2,4})?", haystack)
    effective = re.search(r"(?:wef|effective from)\D{0,25}(20\d{2})(?:\s*[-–/]\s*\d{2,4})?", haystack)
    year = int((admitted or effective).group(1)) if (admitted or effective) else None
    if not programme or year is None:
        return {"applicability_scope": "unclassified"}
    programme_id, degree_level = programme
    return {
        "applicability_scope": "curriculum",
        "programme_id": programme_id,
        "degree_level": degree_level,
        "admission_year_from": year,
        "admission_year_to": 9999,
    }


def extract_program_name(
    metadata,
    cluster,
    subclusters
):

    subcluster_text = (
        " ".join(subclusters)
        .lower()
    )

    PROGRAM_KEYWORDS = [
        "btech",
        "mtech",
        "msc",
        "mdes",      
        "bs-ms",
        "phd",
        "programs",
        "undergraduate",
        "postgraduate",
        "doctoral",
        "dual-degree",
        "dual_degree",
        "pg_admissions",
        "scholarship"
    ]

    is_program_page = any(
        keyword in subcluster_text
        for keyword in PROGRAM_KEYWORDS
    )

    if is_program_page:
        return metadata.get("title")

    return None


def extract_section_type(
    section,
    subclusters
):

    subcluster_text = (
        " ".join(subclusters)
        .lower()
    )

    # --------------------------------------------------
    # Folder-based classification first
    # --------------------------------------------------

    if "scholarship" in subcluster_text:
        return "scholarship"

    if "admission" in subcluster_text:
        return "admissions"

    if "placement" in subcluster_text:
        return "placement"

    if "hostel" in subcluster_text:
        return "facilities"

    if "faculty" in subcluster_text:
        return "faculty"

    # --------------------------------------------------
    # Heading-based classification
    # --------------------------------------------------

    heading_text = " ".join(
        filter(
            None,
            [
                section.get("h1"),
                section.get("h2"),
                section.get("h3")
            ]
        )
    ).lower()

    mappings = {

        "eligibility": [
            "eligibility",
            "eligibility criteria",
            "requirements"
        ],

        "curriculum": [
            "curriculum",
            "course structure",
            "courses"
        ],

        "research": [
            "research",
            "research interests",
            "publications",
            "projects"
        ],

        "contact": [
            "contact",
            "contact information"
        ],

        "facilities": [
            "facilities",
            "food court",
            "hostel facilities"
        ],

        "rules": [
            "rules",
            "regulations",
            "policy"
        ],

        # Fix ME1: fee/fees sections were falling through to "general"
        # section_type because no mapping existed. This prevented the
        # reranker's required_section_boost from firing on fee chunks
        # even when "Fee" appeared in required_sections. Now tagged
        # "admissions" (consistent with their folder-level classification)
        # so the section_type boost also applies.
        "admissions": [
            "fees structure",
            "fee structure",
            "tuition fee",
            "scholarship",
            "financial assistance",
            "admission process",
            "how to apply",
            "application process"
        ]
    }

    for section_type, keywords in mappings.items():

        if any(
            keyword in heading_text
            for keyword in keywords
        ):
            return section_type

    return "general"


def extract_event_metadata(sections):

    metadata = {}

    for section in sections:

        heading = (
            section["h1"]
            or section["h2"]
            or ""
        ).strip()

        if heading.startswith("Date:"):
            metadata["event_date"] = (
                heading.replace(
                    "Date:",
                    ""
                ).strip()
            )

        elif heading.startswith("Venue:"):
            metadata["venue"] = (
                heading.replace(
                    "Venue:",
                    ""
                ).strip()
            )

        elif heading.startswith("Supported by:"):
            metadata["supported_by"] = (
                heading.replace(
                    "Supported by:",
                    ""
                ).strip()
            )

    return metadata
