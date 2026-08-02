import os
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
    #
    # Fix YEAR-UB1 (spot-check finding): this corpus's filenames are almost
    # all snake_case ("..._autumn_2025_page_7.md"), and `_` is a \w
    # character, so a \b...\b year regex never matches "_2025_" — there's no
    # word-boundary transition between an underscore and a digit. That
    # silently skipped this entire step for the majority of course-policy
    # filenames and let extraction fall through to scraped_date (the
    # ingest date), mistagging dozens of "Autumn 2025" documents as 2026
    # simply because they happened to be scraped in 2026. Digit-adjacency
    # lookaround (no digit immediately before/after) still rejects things
    # like "20255" or a stray "42025", but does match "_2025_" and "-2025-".
    for candidate in (title, path_name, path_str, (body or "")[:1000]):
        year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", str(candidate))
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
        year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", str(scraped))
        if year_match:
            return int(year_match.group(1)), None

    return datetime.date.today().year, None


def _detect_ict_cs(identity_text: str):
    """Return ``("btech-ict", "undergraduate", "ict-cs")`` for ICT-CS-only docs.

    ``identity_text`` must be built from the document's IDENTITY — frontmatter
    title, top-level heading, and filename — never from prose deep in the body.
    Branch specialisation is a property of what a document *is*, and the corpus
    signals it there. Generic documents routinely *mention* ICT-CS in prose: the
    main "B.Tech. (ICT) Curriculum and Syllabus" describes both degrees in its
    opening paragraph, and MNC_1st_Yr.md names ICT-CS in a note about shared
    Institute Core courses. Matching on the body tagged both as
    branch_id=ict-cs, which would have hidden the primary ICT curriculum from
    every plain-ICT student: a widening turned into an exclusion, strictly worse
    than the bug being fixed.

    Returns None when the document is not ICT-CS, and also when it is a SHARED
    ICT + ICT-CS document ("ICT_and_ICT-CS_2nd_Yr_Sem3", whose own body says
    "In Semester 3, ICT and ICT-CS follow an identical curriculum"). Those fall
    through to the plain btech-ict pattern with no branch, so both cohorts keep
    them.

    ``identity_text`` arrives lowercased with every non-alphanumeric run
    collapsed to a single space, so "ICT-CS", "ICT_CS" and "ICT CS" all read as
    "ict cs".
    """
    # Shared-cohort phrasings must win over the ICT-CS markers below.
    if re.search(r"\bict\s+(?:and|&|amp)\s+ict\s+cs\b", identity_text):
        return None
    if re.search(r"\bict\s+cs\s+(?:and|&|amp)\s+ict\b", identity_text):
        return None

    ict_cs_markers = (
        # "B.Tech ICT-CS", "BTech(ICT_CS)", "ICT-CS 1st Yr"
        r"\bict\s+cs\b",
        r"\bictcs\b",
        # The full programme name, as used on the programmes-of-study page.
        r"\bict\s+with\s+minor\s+in\s+computational\s+science\b",
        r"\bhonours\s+in\s+ict\b",
        r"\bhonours\s+ict\s+minor\s+computational\s+science\b",
    )
    if any(re.search(marker, identity_text) for marker in ict_cs_markers):
        return ("btech-ict", "undergraduate", "ict-cs")
    return None


def extract_academic_applicability(metadata, file_path, body):
    """Deterministically classify document applicability for student scope.

    "unclassified" is now reachable only via an explicit, reviewed
    frontmatter override (see explicit_scope below) — the heuristic path
    defaults an academic-section document with no detected course or
    programme to "global" rather than excluding it, since a live audit of
    this corpus found that documents naming neither were essentially always
    genuinely general campus-wide content (exam rules, leadership pages,
    procurement, etc.), not programme-specific content that failed
    detection.
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
    # Programme-name regexes below match on whitespace-separated tokens, but
    # real titles/filenames use periods, parentheses, and underscores too
    # (e.g. "B.Tech. (ICT)", "btech_ict"). Collapsing all non-alphanumeric
    # separators to a single space before matching means those variants are
    # actually detected, instead of silently falling through to
    # "unclassified" the way "B.Tech. (ICT) Curriculum and Syllabus" did.
    normalized_haystack = re.sub(r"[^a-z0-9]+", " ", haystack)

    # Fix MX-BODYPIN: which programme a document BELONGS TO is decided from its
    # identity — frontmatter title, filename, and top-level heading — never from
    # prose deep in the body. Matching programme names anywhere in body[:4000]
    # pinned 32 genuinely campus-wide pages to one arbitrary programme, so every
    # student on a different programme lost them: "Grading Policy" became
    # btech-ict-only because it mentions ICT in passing, the careers and
    # leadership pages became phd-only, and the postgraduate/undergraduate
    # programme index pages became single-programme. It also mislabelled the two
    # M.Tech (EC) requirement documents as btech-ece-ai, because the
    # "electronics and communication" alternative in the ECE-AI pattern matched
    # their prose and that pattern is tested first. The H1 is included because
    # the timetable documents carry no frontmatter at all — their identity lives
    # entirely in the heading ("# Timetable — B.Tech ICT-CS — 1st Year").
    heading_match = re.search(r"^#\s+(.+)$", body or "", re.MULTILINE)
    identity_text = re.sub(
        r"[^a-z0-9]+",
        " ",
        " ".join([title, heading_match.group(1) if heading_match else "", path_text]).lower(),
    )

    academic = "academics" in path_text or "academic" in category
    if not academic:
        return {"applicability_scope": "global"}

    # Course-policy documents already carry an explicit course_code in their
    # own frontmatter (see the "Squad D Scraper" course policy files). Scope
    # these by course rather than by programme+admission-year: the same
    # course is frequently taken across several programmes as an elective, it
    # is almost never phrased with "admitted"/"wef <year>" language, and
    # forcing a programme/year match here was silently dropping every course
    # policy document into "unclassified" (i.e. permanently excluded from
    # every logged-in student's retrieval, regardless of programme).
    course_code = metadata.get("course_code")
    if not course_code:
        # Fix MX-COURSECODE: older course-policy files (filenames like
        # "course_policy_it495_exploratorydataanalysis_winter24_....md",
        # or "course_policy_hm_327_...md" where the letters/digits are
        # split across an underscore) never got a course_code frontmatter
        # field — the code only ever lived in the filename, and since
        # underscore is a \w character, a \b-anchored regex on the raw path
        # can never find a boundary immediately before "it495" inside
        # "policy_it495". Splitting on non-alphanumeric characters first and
        # matching each token (and adjacent letter+digit token pairs)
        # avoids that trap.
        tokens = re.split(r"[^a-z0-9]+", os.path.basename(path_text))
        # Words that can precede a 3-digit number without being a course-code
        # prefix (page numbers, "unknown" placeholders in scraped filenames).
        _NON_COURSE_TOKENS = {"page", "unknown", "no", "fig", "img", "pg"}
        for i, tok in enumerate(tokens):
            if tok in _NON_COURSE_TOKENS:
                continue
            m = re.match(r"^([a-z]{2,4})(\d{3})$", tok)
            if m:
                course_code = m.group(1) + m.group(2)
                break
            if re.match(r"^[a-z]{2,4}$", tok) and i + 1 < len(tokens) and re.match(r"^\d{3}$", tokens[i + 1]):
                course_code = tok + tokens[i + 1]
                break
        if course_code:
            course_code = course_code.upper()
    if course_code:
        return {
            "applicability_scope": "course",
            "course_code": str(course_code),
        }

    # (pattern, programme_id, degree_level, branch_id)
    #
    # ICT-CS is a SPECIALISATION of B.Tech. (ICT), not a separate programme —
    # the corpus is explicit about this: the ICT-CS requirements document calls
    # itself "a companion document to the main Academic Requirements for
    # B.Tech. (ICT) Program" and states "All other rules apply uniformly to all
    # B.Tech. (ICT) programs as stated in that document". So it keeps
    # programme_id=btech-ict (which is what makes generic ICT material stay
    # eligible for an ICT-CS student) and is distinguished only by branch_id.
    # It must be matched BEFORE the plain ICT pattern, which would otherwise
    # swallow it.
    programme_patterns = [
        (r"b\.?\s*tech\s*\(?\s*ict\s*\)?", "btech-ict", "undergraduate", None),
        (r"(?:b\.?\s*tech\s*\(?\s*mnc|mathematics and computing)", "btech-mnc", "undergraduate", None),
        (r"(?:b\.?\s*tech\s*\(?\s*evd|electronics and vlsi)", "btech-evd", "undergraduate", None),
        (r"(?:b\.?\s*tech\s*\(?\s*cs\s*(?:and|&)?\s*ai|computer science and artificial intelligence)", "btech-csai", "undergraduate", None),
        (r"(?:b\.?\s*tech\s*\(?\s*ece[\s\-]*ai|electronics and communication)", "btech-ece-ai", "undergraduate", None),
        (r"(?:m\.?\s*sc\s*\(?\s*ds|m\.sc.*data science)", "msc-ds", "postgraduate", None),
        (r"(?:m\.?\s*sc\s*\(?\s*it|m\.sc.*information technology)", "msc-it", "postgraduate", None),
        (r"(?:m\.?\s*sc\s*\(?\s*agri|agriculture analytics)", "msc-agri-analytics", "postgraduate", None),
        (r"m\.?\s*tech\s*\(?\s*ict", "mtech-ict", "postgraduate", None),
        (r"m\.?\s*tech\s*\(?\s*ec\b", "mtech-ec", "postgraduate", None),
        (r"(?:m\.?\s*tech\s*\(?\s*cs\s*(?:and|&)?\s*ml|m\.?\s*tech\s*\(?\s*cs\b)", "mtech-cs-ml", "postgraduate", None),
        (r"bs[\s\-]*ms\s*\(?\s*(?:ds|data science|artificial intelligence)", "bs-ms-dsai", "undergraduate", None),
        (r"bs[\s\-]*ms\s*\(?\s*it|information technology", "bs-ms-it", "undergraduate", None),
        (r"m\.?\s*des\.?\s*\(?\s*cd", "mdes-cd", "postgraduate", None),
        (r"m\.?\s*des\.?\s*\(?\s*iuxd", "mdes-iuxd", "postgraduate", None),
        (r"ph\.?\s*d", "phd", "doctoral", None),
    ]
    ict_cs = _detect_ict_cs(identity_text)
    if ict_cs is not None:
        programme = ict_cs
    else:
        programme = next(
            ((pid, level, branch) for pattern, pid, level, branch in programme_patterns
             if re.search(pattern, identity_text)),
            None,
        )
    if not programme:
        # Fix MX-UNCLASSIFIED: a document under an "academics" path/category
        # that names no course and no programme is, overwhelmingly, a
        # general campus-wide page — examination rules, BTP guidelines,
        # disciplinary guidelines, the academic calendar, semester
        # registration, add/drop guidelines, board of studies, or even
        # leadership pages (President, Founder, Executive Registrar) that
        # simply live under the academics section of the site. A live audit
        # of this corpus found 75 such documents, essentially all of them
        # genuinely general rather than programme-specific, being hard-
        # excluded from every logged-in student's retrieval (while a guest
        # or faculty account — for whom academic_scope is always None —
        # could see them fine). "unclassified" as a fail-closed default was
        # solving the wrong failure mode: it protects against showing
        # programme-A-only content to a programme-B student, but there is no
        # detected programme here to leak in the first place. Defaulting to
        # "global" is the behavior actually intended for this content.
        return {"applicability_scope": "global"}

    admitted = re.search(r"(?:admitted|admission)\D{0,40}(20\d{2})(?:\s*[-–/]\s*\d{2,4})?", haystack)
    effective = re.search(r"(?:wef|effective from)\D{0,25}(20\d{2})(?:\s*[-–/]\s*\d{2,4})?", haystack)
    year = int((admitted or effective).group(1)) if (admitted or effective) else None
    programme_id, degree_level, branch_id = programme
    result = {
        "applicability_scope": "curriculum",
        "programme_id": programme_id,
        "degree_level": degree_level,
        # A confident programme match with no explicit admission-year phrase
        # (e.g. a general curriculum/syllabus overview page) applies to every
        # admission cohort of that programme rather than being thrown away.
        "admission_year_from": year if year is not None else 2000,
        "admission_year_to": 9999,
    }
    if branch_id:
        result["branch_id"] = branch_id
    return result


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


# Issue 4 fix (Scatter-Gather Retrieval): faculty profiles were only chunked
# as raw text with no filterable tag for what a faculty member researches, so
# aggregation queries like "all faculty doing NLP" fell back to top-K semantic
# search, which truncates the full list instead of returning every match.
# This mapping is deliberately a small, exact-match vocabulary (not fuzzy
# NLP) so tagging stays predictable and auditable at ingestion time.
RESEARCH_DOMAIN_KEYWORDS = {
    "Machine Learning": ["machine learning", "deep learning", "neural network"],
    "Natural Language Processing": ["natural language processing", "nlp", "computational linguistics"],
    "Computer Vision": ["computer vision", "image processing", "image analysis"],
    "Data Science": ["data science", "data mining", "big data"],
    "Networks": ["computer networks", "wireless networks", "network security"],
    "Signal Processing": ["signal processing", "dsp"],
    "VLSI": ["vlsi", "microelectronics", "semiconductor"],
    "Robotics": ["robotics", "autonomous systems"],
    "Cybersecurity": ["cybersecurity", "information security", "cryptography"],
    "Internet of Things": ["internet of things", "iot"],
}


def extract_research_domain(text):
    """Tag a faculty profile/research-section chunk with its research
    domain(s), e.g. 'Natural Language Processing', 'Computer Vision', by
    matching RESEARCH_DOMAIN_KEYWORDS against the chunk text.

    Returns a sorted list of matched canonical domain labels, or None if no
    domain keyword is present -- mirrors extract_event_metadata's "only set
    what's actually there" behaviour.
    """
    if not text:
        return None

    text_lower = str(text).lower()

    matched = [
        domain
        for domain, keywords in RESEARCH_DOMAIN_KEYWORDS.items()
        if any(keyword in text_lower for keyword in keywords)
    ]

    return sorted(matched) if matched else None
