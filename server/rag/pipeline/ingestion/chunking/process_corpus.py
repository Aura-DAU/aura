import uuid
import re
from pathlib import Path
import hashlib

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


def convert_tables_to_sentences(text):
    """
    Finds markdown tables in text and converts them into semantic sentences
    to prevent tabular fragmentation during chunking.
    """
    lines = text.split("\n")
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # A markdown table header starts and ends with pipes
        if line.startswith("|") and line.endswith("|"):
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                # A separator line starts and ends with pipes, contains dashes and colons/spaces
                if next_line.startswith("|") and next_line.endswith("|") and "-" in next_line and all(c in " |:-" for c in next_line):
                    # Extracted headers
                    headers = [h.strip() for h in line.split("|")[1:-1]]
                    
                    table_rows = []
                    j = i + 2
                    while j < len(lines):
                        row_line = lines[j].strip()
                        if row_line.startswith("|") and row_line.endswith("|"):
                            row_cells = [c.strip() for c in row_line.split("|")[1:-1]]
                            table_rows.append(row_cells)
                            j += 1
                        else:
                            break
                    
                    # Convert each row to a list of "Header: Value" and join them into a sentence
                    table_sentences = []
                    for row in table_rows:
                        row_parts = []
                        for h, cell in zip(headers, row):
                            if cell:
                                cell_val = cell
                                if cell_val == "✅ Yes":
                                    cell_val = "Yes"
                                elif cell_val == "❌ No":
                                    cell_val = "No"
                                row_parts.append(f"{h}: {cell_val}")
                        if row_parts:
                            table_sentences.append(". ".join(row_parts) + ".")
                    
                    processed_lines.extend(table_sentences)
                    i = j
                    continue
        processed_lines.append(lines[i])
        i += 1
    return "\n".join(processed_lines)
_CANONICAL_FACULTY_NAMES = None

def get_canonical_faculty_names():
    global _CANONICAL_FACULTY_NAMES
    if _CANONICAL_FACULTY_NAMES is not None:
        return _CANONICAL_FACULTY_NAMES
        
    current_dir = Path(__file__).resolve().parent
    # Under server/rag/pipeline/ingestion/chunking/
    data_dir = current_dir.parent.parent.parent.parent.parent / "data"
    f_dir = data_dir / "faculty"
    
    names = set()
    if f_dir.exists():
        for f in f_dir.rglob("*.md"):
            if f.name in ["faculty_list.md", "staff_list.md", "teaching_fellows_list.md", "boards_of_studies_v2.md"]:
                continue
            if "policy" in f.name or "handbook" in f.name or "contract" in f.name or "tenure" in f.name:
                continue
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    m = re.search(r'^title:\s*"([^"]+)"', content, re.MULTILINE)
                    if m:
                        names.add(m.group(1).strip())
                        continue
                    m = re.search(r'^title:\s*([^\r\n]+)', content, re.MULTILINE)
                    if m:
                        names.add(m.group(1).strip().strip("'").strip('"'))
                        continue
            except Exception as e:
                # Non-fatal: if a faculty markdown file cannot be read/parsed,
                # fall back to deriving the name from the filename below.
                _ = e
            name = f.stem.replace("faculty_", "").replace("_", " ").title()
            names.add(name)
            
    _CANONICAL_FACULTY_NAMES = sorted(list(names))
    return _CANONICAL_FACULTY_NAMES


def map_to_canonical_faculty(name):
    canonical_list = get_canonical_faculty_names()
    if not canonical_list or not name:
        return name
        
    from rapidfuzz import fuzz, process
    matches = process.extract(name, canonical_list, scorer=fuzz.WRatio, limit=1)
    if matches:
        best_match = matches[0]
        score = best_match[1]
        if score >= 80.0:
            return best_match[0]
    return name


def extract_faculty_from_text(text):
    """
    Search text for Advisor: ... or similar lines and extract faculty names.
    Also scan text for any matches of canonical faculty names.
    """
    faculty_names = set()
    
    # 1. Scoped advisor lines
    pattern = r"\bAdvisors?\s*:\s*(.*)"
    for line in text.split("\n"):
        m = re.search(pattern, line, re.IGNORECASE)
        if m:
            advisor_str = m.group(1)
            parts = re.split(r",|and", advisor_str, flags=re.IGNORECASE)
            for part in parts:
                part_cleaned = re.sub(
                    r"^(prof\b\.?|professor\b|dr\b\.?|mr\b\.?|ms\b\.?|mrs\b\.?)\s*",
                    "",
                    part.strip(),
                    flags=re.IGNORECASE
                ).strip()
                if part_cleaned:
                    part_cleaned = re.sub(r"\s+", " ", part_cleaned)
                    mapped = map_to_canonical_faculty(part_cleaned)
                    faculty_names.add(mapped)
                    
    # 2. General substring mention matching
    canonical_list = get_canonical_faculty_names()
    for name in canonical_list:
        name_pattern = rf"\b{re.escape(name)}\b"
        if re.search(name_pattern, text, re.IGNORECASE):
            faculty_names.add(name)
            
    return list(faculty_names)


def extract_course_codes_from_text(text):
    """
    Find course codes (2-3 letters followed by 3 digits) in the text.
    """
    codes = set(re.findall(r"\b[A-Z]{2,3}\d{3}\b", text))
    return list(codes)


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

    # Calculate MD5 hash of the file content
    file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

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

    # Frontmatter fields copy
    fm_course_code = metadata.get("course_code")
    fm_semester = metadata.get("semester")
    fm_faculty_name = metadata.get("faculty_name")
    fm_program_name = metadata.get("program_name")
    fm_event_name = metadata.get("event_name")

    chunks = []

    for section in sections:

        section_type = extract_section_type(section, subclusters)

        section_text = ""

        # Extract advisors and mentioned faculty from the section content
        section_faculty = []
        if category == "faculty" and faculty_name:
            section_faculty.append(faculty_name)
        else:
            # Extract mentioned faculty members
            section_faculty.extend(extract_faculty_from_text(section["content"]))
            # Also add frontmatter faculty if defined
            if fm_faculty_name:
                if isinstance(fm_faculty_name, list):
                    section_faculty.extend(fm_faculty_name)
                else:
                    section_faculty.append(fm_faculty_name)
            # Deduplicate
            section_faculty = list(set(section_faculty))

        # Extract course codes from section content and combine with frontmatter course_code
        section_course_codes = extract_course_codes_from_text(section["content"])
        if fm_course_code:
            section_course_codes.append(fm_course_code)
        section_course_codes = list(set(section_course_codes))

        # Prepends contextual lines
        if section_faculty:
            section_text += f"Faculty Name: {', '.join(section_faculty)}\n\n"

        if category == "doctoral scholars" and metadata.get("title"):
            section_text += f"Document Title: {metadata.get('title')}\n"

        if section["h1"]:
            section_text += f"H1: {section['h1']}\n"
        
        if section["h2"]:
            section_text += f"H2: {section['h2']}\n"
        
        if section["h3"]:
            section_text += f"H3: {section['h3']}\n"

        section_text += "\n"
        # Parse table markdown to text sentences
        section_text += convert_tables_to_sentences(section["content"])

        split_chunks = split_section(section_text)

        for chunk_text in split_chunks:
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
                "file_hash": file_hash,

                "scraped_date": metadata.get("scraped_date"),

                "char_length": len(chunk_text),
                "token_estimate": len(chunk_text.split())
            }

            if section_faculty:
                chunk_record["faculty_name"] = section_faculty if len(section_faculty) > 1 else section_faculty[0]

            if section_course_codes:
                chunk_record["course_code"] = section_course_codes if len(section_course_codes) > 1 else section_course_codes[0]

            target_semester = fm_semester or metadata.get("semester")
            if target_semester:
                chunk_record["semester"] = target_semester

            target_program = program_name or fm_program_name
            if target_program:
                chunk_record["program_name"] = target_program

            target_event = event_metadata.get("event_name") or fm_event_name
            if target_event:
                chunk_record["event_name"] = target_event

            if event_metadata:
                chunk_record.update({k: v for k, v in event_metadata.items() if k != "event_name"})

            chunks.append(chunk_record)

    # Add custom curriculum chunks
    curriculum_chunks = extract_curriculum_chunks(body, metadata, file_path)
    for custom in curriculum_chunks:
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
            "file_hash": file_hash, 

            "scraped_date": metadata.get("scraped_date"),

            "char_length": len(custom["text"]),
            "token_estimate": len(custom["text"].split())
        }

        if program_name or fm_program_name:
            chunk_record["program_name"] = program_name or fm_program_name
            
        chunk_record["semester"] = custom.get("semester") or fm_semester
        chunk_record["course_code"] = custom.get("course_code") or fm_course_code
        chunk_record["course_name"] = custom.get("course_name")
        chunk_record["course_type"] = custom.get("course_type")
        chunk_record["credits"] = custom.get("credits")

        chunks.append(chunk_record)

    # Assign contiguous document_id, chunk_index, and total_chunks
    document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path.as_posix()))
    total_chunks = len(chunks)
    for idx, chunk in enumerate(chunks):
        chunk["document_id"] = document_id
        chunk["chunk_index"] = idx
        chunk["total_chunks"] = total_chunks
        # Generate deterministic chunk_id so that future upserts overwrite existing vectors
        chunk["chunk_id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{idx}"))

    return chunks