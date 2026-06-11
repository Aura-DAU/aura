import uuid
from pathlib import Path

from parser import extract_frontmatter
from section_extracter import extract_sections
from chunker import split_section
from metadata_extractors import extract_event_metadata, extract_program_name, extract_section_type


def process_markdown_file(file_path):
    file_path = Path(file_path)
    
    parts = file_path.parts
    data_index = parts.index("data")
    cluster = parts[data_index + 1]

    subclusters = list(
        parts[data_index + 2:-1]
    )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    metadata, body = extract_frontmatter(content)

    sections = extract_sections(body)

    category = metadata.get("category", "").strip().lower()

    faculty_name = None

    if category == "faculty":
        faculty_name = metadata.get("title") or file_path.stem.replace("_", " ").title()

    event_metadata = {}
    
    program_name = extract_program_name(
        metadata,
        cluster,
        subclusters
    )

    if category == "events":
        event_metadata = extract_event_metadata(sections)
        event_metadata["event_name"] = metadata.get("title")

    chunks = []

    for section in sections:

        section_type = extract_section_type(section, subclusters)

        section_text = ""

        if faculty_name:
            section_text += f"Faculty Name: {faculty_name}\n\n"

        if section["h1"]:
            section_text += f"H1: {section['h1']}\n"
        
        if section["h2"]:
            section_text += f"H2: {section['h2']}\n"
        
        if section["h3"]:
            section_text += f"H3: {section['h3']}\n"

        section_text += "\n"
        section_text += section["content"]

        split_chunks = split_section(section_text)
        total = len(split_chunks)

        for idx, chunk_text in enumerate(split_chunks):
            chunk_record = {
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_text,

                "title": metadata.get("title"),
                "url": metadata.get("url"),
                "category": metadata.get("category"),

                "document_type": category,
                "cluster": cluster,
                "subclusters": subclusters,
                
                "h1": section["h1"],
                "h2": section["h2"],
                "h3": section["h3"],
                "section_type": section_type,

                "path": str(file_path),
                "source_file": file_path.name,

                "scraped_date": metadata.get("scraped_date"),

                "chunk_index": idx,
                "total_chunks": total,
                "char_length": len(chunk_text),
                "token_estimate": len(chunk_text.split())
            }

            if faculty_name:
                chunk_record["faculty_name"] = faculty_name

            if event_metadata:
                chunk_record.update(event_metadata)

            if program_name:
                chunk_record["program_name"] = program_name

            chunks.append(chunk_record)

    return chunks