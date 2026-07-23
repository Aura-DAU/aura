import re


def extract_sections(markdown_text):
    """
    Split a markdown body into sections delimited by H1/H2/H3 headings.

    Each returned section dict now includes:
      start_line (int): 1-indexed line number (relative to the body text)
                        at which the section's *content* begins.
      end_line   (int): 1-indexed line number of the last content line
                        (inclusive).  For single-line sections, start == end.

    These values are body-relative.  The caller (process_corpus.py) is
    responsible for adding the frontmatter offset to convert them to
    file-absolute line numbers before storing in Pinecone.
    """

    lines = markdown_text.splitlines()

    sections = []

    current_h1 = None
    current_h2 = None
    current_h3 = None

    current_content: list[str] = []
    section_start_line: int = 1   # 1-indexed, body-relative

    def save_section(end_line: int) -> None:
        content = "\n".join(current_content).strip()
        if not content:
            return

        # end_line is the index of the line that triggered the heading that
        # *closes* this section, so the real last content line is end_line - 1.
        # We clamp to at least section_start_line to avoid negative spans.
        real_end = max(section_start_line, end_line - 1)

        sections.append({
            "h1": current_h1,
            "h2": current_h2,
            "h3": current_h3,
            "content": "\n".join(current_content).strip(),
            "start_line": section_start_line,
            "end_line": real_end,
        })

    for line_num, line in enumerate(lines, start=1):

        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)

        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            if level == 1:
                save_section(end_line=line_num)
                current_h1 = title
                current_h2 = None
                current_h3 = None
                current_content = []
                section_start_line = line_num + 1

            elif level == 2:
                save_section(end_line=line_num)
                current_h2 = title
                current_h3 = None
                current_content = []
                section_start_line = line_num + 1

            elif level == 3:
                save_section(end_line=line_num)
                current_h3 = title
                current_content = []
                section_start_line = line_num + 1

            else:
                # Fix D: H4–H6 headings were previously treated as plain body
                # text (falling to the else branch below), losing structural
                # context like "Research Area: VLSI" on faculty pages.
                # Now fold them into the current section content as bold lines
                # so embeddings and BM25 capture the semantic signal.
                current_content.append(f"**{title}**")

        else:
            current_content.append(line)

    # Flush the final section — end_line is one past the last line of the body
    save_section(end_line=len(lines) + 1)

    return sections