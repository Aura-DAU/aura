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

            level = len(
                heading_match.group(1)
            )

            title = (
                heading_match.group(2)
                .strip()
            )

            if level == 1:
                save_section()
                current_h1 = title
                current_h2 = None
                current_h3 = None
                current_content = []

            elif level == 2:
                save_section()
                current_h2 = title
                current_h3 = None
                current_content = []

            elif level == 3:
                save_section()
                current_h3 = title
                current_content = []

            else:
                # Fix D: H4–H6 headings were previously treated as plain body
                # text (falling to the else branch below), losing structural
                # context like "Research Area: VLSI" on faculty pages.
                # Now fold them into the current section content as bold lines
                # so embeddings and BM25 capture the semantic signal.
                current_content.append(f"**{title}**")

        else:
            current_content.append(line)

    save_section()

    return sections