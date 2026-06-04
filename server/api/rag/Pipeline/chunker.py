import os
import re
import json
import yaml
import tiktoken

MAX_TOKENS = 600
OVERLAP_TOKENS = 75
MIN_TOKENS = 40

ENCODING = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(ENCODING.encode(text))


def split_large_section(section):
    """
    Split section into token chunks with overlap
    """

    if count_tokens(section) <= MAX_TOKENS:
        return [section]
    
    tokens = ENCODING.encode(section)

    chunks = []

    start = 0

    while start < len(tokens):
        end = start + MAX_TOKENS
        chunk_tokens = tokens[start:end]
        chunks.append(ENCODING.decode(chunk_tokens))

        if end >= len(tokens):
            break

        start = end - OVERLAP_TOKENS

    return chunks


def extract_sections(markdown_text):
    """
    Create sections while preserving heading hierarchy
    """

    lines = markdown_text.splitlines()
    sections = []
    heading_stack = []
    current_content = []

    for line in lines:
        heading_match = re.match(
            r'^(#{1,6})\s+(.*)',
            line
        )

        if heading_match:
            if current_content:
                sections.append(
                    {
                        "heading_path": heading_stack.copy(),
                        "content": "\n".join(current_content).strip()
                    }
                )

                current_content = []
            
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()

            heading_stack = heading_stack[:level-1]
            heading_stack.append(heading)
            current_content.append(line)

        else:
            current_content.append(line)

    if current_content:
        sections.append(
            {
                "heading_path": heading_stack.copy(),
                "content": "\n".join(current_content).strip()
            }
        )
    
    return sections

def remove_heading_lines(text):
    return re.sub(
        r'^#{1,6}\s+.*$',
        '',
        text,
        flags=re.MULTILINE
    ).strip()



def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}

    frontmatter_match = re.match(
        r'^---\n(.*?)\n---\n',
        content,
        re.DOTALL
    )

    if frontmatter_match:
        try:
            metadata = yaml.safe_load(frontmatter_match.group(1))

        except yaml.YAMLError as e:
            print(f"\nYAML ERROR IN FILE: {filepath}")
            print(e)

            return []

        content = content[frontmatter_match.end():]

    doc_id = (
        os.path.splitext(os.path.basename(filepath))[0].lower()
    )

    sections = extract_sections(content)

    chunks = []

    chunk_counter = 1

    for idx, section in enumerate(sections):
        heading_path = section["heading_path"]

        section_chunks = split_large_section(section["content"])

        for sub_idx, subsection in enumerate(section_chunks):
            heading_context = ""

            if heading_path:
                heading_context = (
                    " > ".join(heading_path)
                    + "\n\n"
                )

                section_path = (
                    " > ".join(heading_path)
                )

            clean_content = remove_heading_lines(subsection)

            if count_tokens(clean_content) < MIN_TOKENS:
                continue

            if not clean_content:
                continue

            relative_path = os.path.relpath(filepath, "../../data")

            safe_path = (
                relative_path
                .replace("\\", "_")
                .replace("/", "_")
                .replace(".md", "")
                .lower()
            )

            chunk_id = f"{safe_path}_{chunk_counter:04d}"

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "source_file": os.path.basename(filepath),
                    "title": metadata.get("title", ""),
                    "category": metadata.get("category", ""),
                    "url": metadata.get("url", ""),
                    "scraped_date": metadata.get("scraped_date", ""),
                    "heading": heading_path[-1] if heading_path else "",
                    "heading_path": heading_path,
                    "section_path": heading_context.strip() if heading_context else "",
                    "token_count": count_tokens(clean_content),
                    "content": heading_context + clean_content
                }
            )
            chunk_counter += 1

    return chunks


def process_directory(directory):
    all_chunks = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)

                print(f"Processing {file}")

                all_chunks.extend(process_file(filepath))

    return all_chunks


if __name__ == "__main__":
    chunks = process_directory("../../data")

    os.makedirs("knowledge_index", exist_ok=True)

    with open("knowledge_index/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nGenerated {len(chunks)} chunks")

    token_counts = [c["token_count"] for c in chunks]

    print(min(token_counts))
    print(max(token_counts))
    print(sum(token_counts)/len(token_counts))

