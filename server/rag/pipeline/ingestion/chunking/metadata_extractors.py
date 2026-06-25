import re


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
        "mdes",      # Fix I: was missing comma — previously concatenated with "bs-ms" into "mdesbs-ms"
        "bs-ms",
        "phd",
        "programs",
        "undergraduate",
        "postgraduate",
        "doctoral",
        "dual-degree"
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