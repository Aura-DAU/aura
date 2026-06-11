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