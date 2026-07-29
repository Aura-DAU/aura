import re


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
