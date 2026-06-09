import re


def extract_sections(markdown_text):

    lines = markdown_text.splitlines()

    sections = []

    current_h1 = None
    current_h2 = None
    current_h3 = None

    current_content = []

    def save_section():
        content = "\n".join(current_content).strip()

        if not content:
            return

        sections.append({
            "h1": current_h1,
            "h2": current_h2,
            "h3": current_h3,
            "content": "\n".join(
                current_content
            ).strip()
        })

    for line in lines:

        heading_match = re.match(
            r'^(#{1,6})\s+(.*)',
            line
        )

        if heading_match:

            save_section()

            level = len(
                heading_match.group(1)
            )

            title = (
                heading_match.group(2)
                .strip()
            )

            current_content = []

            if level == 1:
                current_h1 = title
                current_h2 = None
                current_h3 = None

            elif level == 2:
                current_h2 = title
                current_h3 = None

            elif level == 3:
                current_h3 = title

        else:
            current_content.append(line)

    save_section()

    return sections