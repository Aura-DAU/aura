import uuid
import re
from pathlib import Path

from parser import extract_frontmatter
from section_extracter import extract_sections
from chunker import split_section
from metadata_extractors import extract_event_metadata, extract_program_name, extract_section_type


def extract_curriculum_chunks(body, metadata, file_path):
    lines = body.split("\n")
    current_semester = None
    table_started = False
    headers = []
    rows = []
    tables = []
    
    for line in lines:
        line_strip = line.strip()
        semester_match = re.match(
            r"^#{2,6}\s*Semester\s+([IVX]+|\d+)$",
            line_strip,
            re.IGNORECASE
        )

        if semester_match:
            current_semester = semester_match.group(1).upper()

        if line_strip.startswith("|"):
            if not table_started:
                table_started = True
                headers = [h.strip() for h in line_strip.split("|")[1:-1]]
            else:
                if re.match(r"^\|[\s\-\|]+$", line_strip):
                    continue
                row_cells = [c.strip() for c in line_strip.split("|")[1:-1]]
                rows.append(row_cells)
        else:
            if table_started:
                tables.append((headers, rows, current_semester))
                table_started = False
                headers = []
                rows = []
    if table_started:
        tables.append((headers, rows, current_semester))

    custom_chunks = []
    semester_courses = {}
    
    roman_map = {
        "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII",
        "i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V", "vi": "VI", "vii": "VII", "viii": "VIII"
    }

    for headers, rows, table_semester in tables:
        header_lower = [h.lower() for h in headers]
        
        has_code = any(
            ("code" in h) or (h == "category") 
            for h in header_lower
        )
        has_name = any("name" in h or "title" in h or "subject" in h for h in header_lower)
        
        if not (has_code and has_name):
            continue
            
        col_sem = -1
        col_code = -1
        col_name = -1
        col_type = -1
        col_credits = -1
        
        for idx, h in enumerate(header_lower):
            if "sem" in h:
                col_sem = idx
            elif "code" in h or h == "category":
                col_code = idx
            elif "name" in h or "title" in h or "subject" in h:
                col_name = idx
            elif "type" in h:
                col_type = idx
            elif "l-t-p-c" in h or "credit" in h or "c" == h:
                col_credits = idx
                
        for row in rows:
            if len(row) <= max(col_code, col_name):
                continue
            course_code = row[col_code].strip()
            # if col_code != -1 and h == "category":
            #     if not re.match(
            #         r"^#{2,6}\s*Semester\s+([IVX]+|\d+)$",
            #         course_code,
            #         re.IGNORECASE
            #     ): 
            #         continue

            course_name = row[col_name].strip()
            
            if not course_code or not course_name or course_code == "Course Code":
                continue
                
            if col_sem != -1 and col_sem < len(row):
                sem_raw = row[col_sem].strip()
            else:
                sem_raw = table_semester or ""

            sem_roman = roman_map.get(sem_raw.lower(), sem_raw)
            if not sem_roman:
                sem_roman = "I"
                
            credits_raw = row[col_credits].strip() if col_credits != -1 and col_credits < len(row) else ""
            credits_val = credits_raw
            if "-" in credits_raw:
                credits_val = credits_raw.split("-")[-1]
            elif not credits_raw:
                credits_val = "N/A"
                
            course_type = row[col_type].strip() if col_type != -1 and col_type < len(row) else "Core"
            
            chunk_text = (
                f"Course Name: {course_name}\n"
                f"Course Code: {course_code}\n"
                f"Semester: {sem_roman}\n"
                f"Credits: {credits_val}"
            )
            
            custom_chunks.append({
                "text": chunk_text,
                "h1": "Curriculum Course Details",
                "h2": f"{course_name} ({course_code})",
                "h3": f"Semester {sem_roman}",
                "section_type": "curriculum",
                "semester": sem_roman,
                "course_code": course_code,
                "course_name": course_name,
                "course_type": course_type,
                "credits": credits_val
            })
            
            if sem_roman not in semester_courses:
                semester_courses[sem_roman] = []
            semester_courses[sem_roman].append(
                f"- {course_code} | {course_name} ({course_type}, Credits: {credits_val})"
            )
            
    for sem, courses_list in semester_courses.items():
        courses_str = "\n".join(courses_list)
        chunk_text = (
            f"Semester {sem} Chunk\n"
            f"Courses taught in Semester {sem}:\n"
            f"{courses_str}"
        )
        custom_chunks.append({
            "text": chunk_text,
            "h1": "Semester Curriculum Overview",
            "h2": f"Semester {sem} Courses",
            "h3": None,
            "section_type": "curriculum",
            "semester": sem,
            "course_code": None,
            "course_name": None,
            "course_type": None,
            "credits": None
        })
        
    return custom_chunks


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

    # Add custom curriculum chunks
    curriculum_chunks = extract_curriculum_chunks(body, metadata, file_path)
    total_custom = len(curriculum_chunks)
    for idx, custom in enumerate(curriculum_chunks):
        chunk_record = {
            "chunk_id": str(uuid.uuid4()),
            "text": custom["text"],

            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "category": metadata.get("category"),

            "document_type": category,
            "cluster": cluster,
            "subclusters": subclusters,
            
            "h1": custom["h1"],
            "h2": custom["h2"],
            "h3": custom["h3"],
            "section_type": custom["section_type"],

            "path": str(file_path),
            "source_file": file_path.name,

            "scraped_date": metadata.get("scraped_date"),

            "chunk_index": idx,
            "total_chunks": total_custom,
            "char_length": len(custom["text"]),
            "token_estimate": len(custom["text"].split())
        }

        if program_name:
            chunk_record["program_name"] = program_name

        chunk_record["semester"] = custom.get(
            "semester"
        )

        chunk_record["course_code"] = custom.get(
            "course_code"
        )

        chunk_record["course_name"] = custom.get(
            "course_name"
        )

        chunk_record["course_type"] = custom.get(
            "course_type"
        )

        chunk_record["credits"] = custom.get(
            "credits"
        )

        chunks.append(chunk_record)

    return chunks