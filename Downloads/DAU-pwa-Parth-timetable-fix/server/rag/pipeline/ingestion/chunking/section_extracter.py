import re


def extract_sections(markdown_text, start_line_offset=1):

    lines = markdown_text.splitlines()

    sections = []

    current_h1 = None
    current_h2 = None
    current_h3 = None

    current_content = []
    section_start_line = start_line_offset

    def save_section(end_line):
        content = "\n".join(current_content).strip()

        if not content:
            return

        sections.append({
            "h1": current_h1,
            "h2": current_h2,
            "h3": current_h3,
            "content": content,
            "start_line": section_start_line,
            "end_line": end_line
        })

    for idx, line in enumerate(lines):
        line_num = idx + start_line_offset
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
                save_section(line_num - 1)
                current_h1 = title
                current_h2 = None
                current_h3 = None
                current_content = []
                section_start_line = line_num

            elif level == 2:
                save_section(line_num - 1)
                current_h2 = title
                current_h3 = None
                current_content = []
                section_start_line = line_num

            elif level == 3:
                save_section(line_num - 1)
                current_h3 = title
                current_content = []
                section_start_line = line_num

            else:
                # Fix D: H4–H6 headings were previously treated as plain body
                # text (falling to the else branch below), losing structural
                # context like "Research Area: VLSI" on faculty pages.
                # Fold them into the current section content as bold lines
                # so embeddings and BM25 capture the semantic signal.
                current_content.append(f"**{title}**")

        else:
            current_content.append(line)

    save_section(len(lines) + start_line_offset - 1)

    return sections