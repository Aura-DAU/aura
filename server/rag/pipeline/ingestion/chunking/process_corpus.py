from __future__ import annotations
import sys
import importlib.abc
import importlib.util
import uuid
import re
import logging
from pathlib import Path

# Python 3.9 compatibility hook for metadata_extractors without mutating files on disk
class _FutureAnnotationsFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "metadata_extractors":
            mod_path = Path(__file__).parent / "metadata_extractors.py"
            if mod_path.exists():
                class _Loader(importlib.abc.Loader):
                    def exec_module(self, module):
                        with open(mod_path, "r", encoding="utf-8") as f:
                            code_text = "from __future__ import annotations\n" + f.read()
                        code_obj = compile(code_text, str(mod_path), "exec")
                        exec(code_obj, module.__dict__)
                return importlib.util.spec_from_loader(fullname, _Loader())
        return None

if "metadata_extractors" not in sys.modules:
    sys.meta_path.insert(0, _FutureAnnotationsFinder())

from parser import extract_frontmatter
from section_extracter import extract_sections
from chunker import split_section
from chunk_id_generator import generate_deterministic_chunk_id
from metadata_extractors import (
    extract_academic_applicability,
    extract_event_metadata,
    extract_program_name,
    extract_section_type,
    resolve_document_academic_year,
)
from program_names import canonicalize_program_value

logger = logging.getLogger(__name__)

# Global metrics for entity-first ingestion quality report
INGESTION_METRICS = {
    "files_processed": 0,
    "chunks_generated": 0,
    "total_characters": 0,
    "total_tokens": 0,
    "max_chunk_tokens": 0,
    "h3_splits": 0,
    "h4_splits": 0,
    "table_row_splits": 0,
    "faq_splits": 0,
    "bold_entity_splits": 0,
    "course_chunks": 0,
    "club_chunks": 0,
    "committee_chunks": 0,
    "faculty_chunks": 0,
}


def print_ingestion_quality_report():
    """Prints a detailed Quality Report summarizing entity-first chunking results."""
    m = INGESTION_METRICS
    chunks_count = m["chunks_generated"]
    avg_tokens = (m["total_tokens"] / chunks_count) if chunks_count > 0 else 0
    avg_chars = (m["total_characters"] / chunks_count) if chunks_count > 0 else 0

    print("\n" + "=" * 65)
    print("      AURA INGESTION PIPELINE — CHUNKING QUALITY REPORT      ")
    print("=" * 65)
    print(f"Files Processed        : {m['files_processed']}")
    print(f"Total Chunks Generated : {chunks_count}")
    print(f"Average Chunk Tokens   : {avg_tokens:.1f} tokens")
    print(f"Average Chunk Length   : {avg_chars:.1f} chars")
    print(f"Maximum Chunk Size     : {m['max_chunk_tokens']} tokens")
    print("-" * 65)
    print("ENTITY SPLIT METRICS:")
    print(f"  • H3 Entity Splits   : {m['h3_splits']}")
    print(f"  • H4 Entity Splits   : {m['h4_splits']}")
    print(f"  • Bold Entity Splits : {m['bold_entity_splits']}")
    print(f"  • Table Row Splits   : {m['table_row_splits']}")
    print(f"  • FAQ Pair Splits    : {m['faq_splits']}")
    print("-" * 65)
    print("ENTITY TYPE BREAKDOWN:")
    print(f"  • Club Chunks        : {m['club_chunks']}")
    print(f"  • Faculty Chunks     : {m['faculty_chunks']}")
    print(f"  • Course Chunks      : {m['course_chunks']}")
    print(f"  • Committee Chunks   : {m['committee_chunks']}")
    print("=" * 65 + "\n")


def _normalize_metadata_value(val):
    """Helper to clean, trim, deduplicate, and return deterministic string or sorted list."""
    if val is None:
        return None
    if isinstance(val, (list, tuple, set)):
        cleaned = []
        seen = set()
        for item in val:
            if item is None:
                continue
            s = str(item).strip()
            if s and s not in seen:
                seen.add(s)
                cleaned.append(s)
        if not cleaned:
            return None
        return cleaned[0] if len(cleaned) == 1 else sorted(cleaned)
    s = str(val).strip()
    return s if s else None


def _extract_program_name_from_text(text):
    """Extracts Program(s) / Program name explicitly declared in body text."""
    patterns = [
        r"(?:Program\(s\)|Programs?|Degree|Branch)\s*:\s*([^\r\n]+)",
        r"\b(B\.?\s*Tech\.?\s*(?:ICT-CS|ICT|MnC|EAS)?|M\.?\s*Tech\.?\s*(?:ICT|EC)?|M\.?\s*Sc\.?\s*(?:IT|DS|AA)|Ph\.?\s*D\.?)\b"
    ]
    extracted = []
    seen = set()
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            parts = re.split(r",|/|and", m, flags=re.IGNORECASE)
            for p in parts:
                p_clean = p.strip()
                if p_clean and len(p_clean) > 1 and p_clean not in seen:
                    seen.add(p_clean)
                    extracted.append(p_clean)
    return extracted


def extract_curriculum_chunks(body, metadata, file_path):
    """Preserved curriculum extraction logic for course catalogues and syllabi."""
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
            course_code_raw = row[col_code].strip()
            course_name = row[col_name].strip()
            
            if not course_code_raw or not course_name or course_code_raw.lower() == "course code":
                continue
                
            course_code = re.sub(r"[\s\-]", "", course_code_raw).upper()
                
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
    """Converts markdown table rows into descriptive key-value sentences."""
    lines = text.split("\n")
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|"):
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line.startswith("|") and next_line.endswith("|") and "-" in next_line and all(c in " |:-" for c in next_line):
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


# Non-entity structural H4 headers that should NOT cause H4 entity splits
STRUCTURAL_H4_TITLES = {
    "description", "overview", "objectives", "events", "activities",
    "rules", "guidelines", "eligibility", "requirements", "details",
    "background", "about", "scope", "responsibilities", "members", "contact",
    "procedure", "process", "note", "notes", "summary", "fees", "structure"
}


def _split_content_by_subheadings(content):
    """
    H3 / H4 Rule Tuning:
    - Always splits by H3 (###) by default.
    - Splits by H4 (####) ONLY when H4 represents an independent semantic entity
      (e.g., a specific named entity or person), NOT for structural fields like Description/Objectives.
    """
    lines = content.split("\n")
    sub_entities = []
    
    current_h3 = None
    current_h4 = None
    current_lines = []
    
    for line in lines:
        match = re.match(r"^(#{3,4})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            title_lower = title.lower()

            # Check if this H4 is a non-entity structural field
            is_structural_h4 = (
                level == 4 and (
                    title_lower in STRUCTURAL_H4_TITLES or
                    any(title_lower.startswith(s) for s in ["description", "overview", "objective", "event", "rule", "note"])
                )
            )

            # Split only on H3, or on entity-level H4
            if level == 3 or (level == 4 and not is_structural_h4):
                if current_lines or current_h3 or current_h4:
                    sub_entities.append({
                        "h3": current_h3,
                        "h4": current_h4,
                        "content": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                
                if level == 3:
                    current_h3 = title
                    current_h4 = None
                    INGESTION_METRICS["h3_splits"] += 1
                else:
                    current_h4 = title
                    INGESTION_METRICS["h4_splits"] += 1
            else:
                # Treat structural H4 as body text under current H3
                current_lines.append(f"#### {title}")
        else:
            current_lines.append(line)
            
    if current_lines or current_h3 or current_h4:
        sub_entities.append({
            "h3": current_h3,
            "h4": current_h4,
            "content": "\n".join(current_lines).strip()
        })
        
    return sub_entities if sub_entities else [{"h3": None, "h4": None, "content": content}]


def _is_directory_table_by_headers(sub_content, relative_path="", title=""):
    """
    Structure-Based Directory Table Detection:
    Inspects table header columns to detect directory/roster tables (Clubs, Committees, Contacts, Faculty, Staff)
    rather than relying solely on filenames.
    """
    lines = [l.strip() for l in sub_content.split("\n") if l.strip().startswith("|")]
    if not lines:
        return False

    header_line = lines[0]
    headers = [h.strip().lower() for h in header_line.split("|")[1:-1]]
    header_str = " ".join(headers)

    # Exclude curriculum / course list tables
    if any(k in header_str for k in ["l-t-p-c", "credits", "semester", "course code"]):
        return False

    dir_header_keywords = [
        "name", "designation", "email", "phone", "contact", "convenor", "convener",
        "mentor", "advisor", "club", "committee", "office", "post", "position",
        "role", "room", "member", "scholarship", "head", "chair", "deputy"
    ]

    matches = sum(1 for k in dir_header_keywords if any(k in h for h in headers))
    if matches >= 1:
        return True

    path_title = (relative_path + " " + title).lower()
    return any(k in path_title for k in ["club", "committee", "contact", "faculty", "staff", "desk", "directory"])


def _split_directory_table_rows(content, headers_context):
    """
    Table Row Rule: Converts table rows of directory tables into individual entity items
    so 1 row = 1 semantic entity chunk.
    """
    lines = content.split("\n")
    entities = []
    i = 0
    non_table_lines = []
    
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line.startswith("|") and next_line.endswith("|") and "-" in next_line:
                headers = [h.strip() for h in line.split("|")[1:-1]]
                j = i + 2
                while j < len(lines):
                    row_line = lines[j].strip()
                    if row_line.startswith("|") and row_line.endswith("|"):
                        cells = [c.strip() for c in row_line.split("|")[1:-1]]
                        row_str = ". ".join(f"{h}: {c}" for h, c in zip(headers, cells) if c)
                        if row_str:
                            entities.append(f"{headers_context}\n{row_str}")
                            INGESTION_METRICS["table_row_splits"] += 1
                        j += 1
                    else:
                        break
                i = j
                continue
        non_table_lines.append(lines[i])
        i += 1
        
    remainder = "\n".join(non_table_lines).strip()
    if remainder:
        entities.append(remainder)
    return entities if entities else [content]


def _split_faqs(content):
    """
    Enhanced FAQ Detection: Splits Q&A pairs (supporting Q:, Question:, ### Question, **Q:**, **Question:**).
    """
    pattern = r"(?:^|\n)(?:\*{1,2}|\#{1,4})?\s*(?:Q|Question)\s*\d*[\.\:]\s*(.*?)(?=\n(?:\*{1,2}|\#{1,4})?\s*(?:Q|Question)\s*\d*[\.\:]|\Z)"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    if len(matches) > 1:
        INGESTION_METRICS["faq_splits"] += len(matches)
        return [f"Question: {m.strip()}" for m in matches if m.strip()]
    return [content]


def _split_bold_entity_blocks(content):
    """
    Semantic Entity Boundary Detection:
    Splits sections without H3 into independent semantic entity blocks when items are formatted as
    bold headers (e.g. **Hostel A:** ..., **Scholarship 1:** ...).
    """
    pattern = r"(?:^|\n)(?:\d+\.\s*)?\*\*(.*?)\*\*\s*[\:\-]?\s*"
    matches = list(re.finditer(pattern, content))
    if len(matches) > 1:
        blocks = []
        for idx in range(len(matches)):
            start_pos = matches[idx].start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            block_text = content[start_pos:end_pos].strip()
            if block_text:
                blocks.append(block_text)
                INGESTION_METRICS["bold_entity_splits"] += 1
        if blocks:
            return blocks
    return [content]


def _adaptive_split_entity(entity_text, max_tokens=256):
    """
    Adaptive Chunking:
    - If entity <= 256 tokens -> Return exactly 1 chunk.
    - If entity > 256 tokens -> Split semantically preserving structure (Paragraphs -> Bullets -> Lines -> Token fallback).
    """
    words = entity_text.split()
    if len(words) <= max_tokens:
        return [entity_text]

    # 1. Split by Paragraph Boundaries (\n\n)
    paragraphs = [p.strip() for p in entity_text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        chunks = []
        current = []
        curr_len = 0
        for p in paragraphs:
            p_len = len(p.split())
            if curr_len + p_len <= max_tokens:
                current.append(p)
                curr_len += p_len
            else:
                if current:
                    chunks.append("\n\n".join(current))
                if p_len > max_tokens:
                    chunks.extend(_split_by_lines_or_bullets(p, max_tokens))
                    current = []
                    curr_len = 0
                else:
                    current = [p]
                    curr_len = p_len
        if current:
            chunks.append("\n\n".join(current))
        return chunks

    # 2. Line / Bullet splitting
    return _split_by_lines_or_bullets(entity_text, max_tokens)


def _split_by_lines_or_bullets(text, max_tokens=256):
    """Splits large text blocks by bullet points or line boundaries."""
    lines = text.split("\n")
    chunks = []
    current = []
    curr_len = 0
    for line in lines:
        l_len = len(line.split())
        if curr_len + l_len <= max_tokens:
            current.append(line)
            curr_len += l_len
        else:
            if current:
                chunks.append("\n".join(current))
            if l_len > max_tokens:
                # Raw token fallback
                chunks.extend(split_section(line))
                current = []
                curr_len = 0
            else:
                current = [line]
                curr_len = l_len
    if current:
        chunks.append("\n".join(current))
    return chunks


_CANONICAL_FACULTY_NAMES = None

def get_canonical_faculty_names():
    global _CANONICAL_FACULTY_NAMES
    if _CANONICAL_FACULTY_NAMES is not None:
        return _CANONICAL_FACULTY_NAMES
        
    current_dir = Path(__file__).resolve().parent
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
    faculty_names = set()
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
                    
    canonical_list = get_canonical_faculty_names()
    for name in canonical_list:
        name_pattern = rf"\b{re.escape(name)}\b"
        if re.search(name_pattern, text, re.IGNORECASE):
            faculty_names.add(name)
            
    return list(faculty_names)


def extract_course_codes_from_text(text):
    matches = re.findall(r"\b([A-Z]{2,3})[\s\-]?(\d{3})\b", text)
    codes = set(f"{m[0]}{m[1]}" for m in matches)
    return list(codes)


def find_line_range_in_file(chunk_text, file_lines, section_start=1, section_end=None):
    lines_to_search = []
    for line in chunk_text.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith(("H1:", "H2:", "H3:", "H4:", "Faculty Name:", "Document Title:", "Course Name:", "Course Code:", "Semester:", "Credits:")):
            continue
        line_clean = line_clean.replace("**", "").replace("__", "").replace("*", "").strip()
        if len(line_clean) > 5:
            lines_to_search.append(line_clean)

    if not lines_to_search:
        return section_start, section_end or len(file_lines)

    first_match = None
    last_match = None

    search_range_start = max(0, section_start - 1)
    search_range_end = len(file_lines) if section_end is None else min(len(file_lines), section_end)

    for phrase in lines_to_search:
        for idx in range(search_range_start, search_range_end):
            file_line = file_lines[idx].strip()
            if not file_line:
                continue
            if phrase in file_line or file_line in phrase:
                if first_match is None or idx < first_match:
                    first_match = idx
                if last_match is None or idx > last_match:
                    last_match = idx
                break

    if first_match is not None and last_match is not None:
        return first_match + 1, last_match + 1
    elif first_match is not None:
        return first_match + 1, first_match + 1
    
    return section_start, section_end or len(file_lines)


def process_markdown_file(file_path):
    file_path = Path(file_path)
    INGESTION_METRICS["files_processed"] += 1
    
    parts = file_path.parts
    data_index = parts.index("data")
    cluster = parts[data_index + 1]
    relative_path = "/".join(parts[data_index:])
    subclusters = list(parts[data_index + 2:-1])

    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    file_lines = raw_content.replace("\r\n", "\n").split("\n")

    metadata, body = extract_frontmatter(raw_content)
    academic_applicability = extract_academic_applicability(metadata, file_path, body)

    content_clean = raw_content.lstrip("\ufeff").replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n", content_clean, re.DOTALL)
    frontmatter_offset = match.group(0).count('\n') if match else 0

    document_year, academic_year = resolve_document_academic_year(metadata, file_path, body)

    authorization = metadata.get("authorization") or metadata.get("authorisation") or ["public"]
    if isinstance(authorization, str):
        authorization = [authorization]

    sections = extract_sections(body, start_line_offset=frontmatter_offset + 1)
    category = metadata.get("category", "").strip().lower()

    faculty_name = None
    if category == "faculty":
        faculty_name = metadata.get("title") or file_path.stem.replace("_", " ").title()

    event_metadata = {}

    # ── DETERMINISTIC METADATA RESOLUTION (PRECEDENCE ENFORCING) ──
    # 1. Program Name Precedence: Frontmatter -> Structured Body Text -> Fallback Inference
    fm_program = metadata.get("program_name") or metadata.get("programs") or metadata.get("program")
    body_programs = _extract_program_name_from_text(body)
    inferred_program = extract_program_name(metadata, cluster, subclusters)
    
    # Canonicalize at each precedence level independently: a frontmatter value
    # that canonicalizes to nothing must fall through to body text, not win
    # the precedence race with a value retrieval can never filter on.
    effective_program_name = (
        canonicalize_program_value(_normalize_metadata_value(fm_program)) or
        canonicalize_program_value(_normalize_metadata_value(body_programs)) or
        canonicalize_program_value(inferred_program)
    )

    # 2. Semester Precedence: Frontmatter (Highest) -> Metadata -> None
    fm_semester = metadata.get("semester")
    effective_semester = _normalize_metadata_value(fm_semester)

    # 3. Course Code Precedence: Document-Type Aware
    fm_course_code_raw = metadata.get("course_code")
    fm_course_code = None
    if fm_course_code_raw:
        if isinstance(fm_course_code_raw, list):
            fm_course_code = [re.sub(r"[\s\-]", "", str(c)).upper() for c in fm_course_code_raw if c]
        else:
            fm_course_code = re.sub(r"[\s\-]", "", str(fm_course_code_raw)).upper()
            
    is_single_course_doc = (
        bool(fm_course_code) or
        category in ["courses", "course_policy", "course"] or
        "course_policy" in relative_path.lower()
    )

    if category == "events":
        event_metadata = extract_event_metadata(sections)
        event_metadata["event_name"] = metadata.get("title")

    fm_faculty_name = metadata.get("faculty_name")
    fm_event_name = metadata.get("event_name")

    chunks = []

    # Check if custom curriculum extraction will generate chunks for this document
    has_curriculum_chunks = ("curriculum" in relative_path.lower() or "syllabus" in relative_path.lower())

    for section in sections:
        section_type = extract_section_type(section, subclusters)

        # Curriculum Duplication Guard: Skip raw section processing if section_type is curriculum
        if section_type == "curriculum" and has_curriculum_chunks:
            continue
        
        # ── ENTITY DETECTION STAGE ──
        # Step A: Split section content by H3 / H4 sub-headings (selective H4 splitting)
        sub_heading_blocks = _split_content_by_subheadings(section["content"])

        for sub_block in sub_heading_blocks:
            effective_h3 = sub_block["h3"] or section["h3"]
            effective_h4 = sub_block["h4"]
            sub_content = sub_block["content"]

            # Step B: Structure-Based Directory Table Detection vs FAQ vs Bold Entity Detection
            headers_ctx = f"H1: {section['h1'] or ''}\nH2: {section['h2'] or ''}\nH3: {effective_h3 or ''}".strip()
            is_dir_table = _is_directory_table_by_headers(sub_content, relative_path, metadata.get("title") or "")
            
            if is_dir_table and "|" in sub_content:
                raw_entity_blocks = _split_directory_table_rows(sub_content, headers_ctx)
            else:
                converted_content = convert_tables_to_sentences(sub_content)
                faq_blocks = _split_faqs(converted_content)
                raw_entity_blocks = []
                for b in faq_blocks:
                    # Semantic Boundary Detection for sections without H3
                    if not effective_h3:
                        raw_entity_blocks.extend(_split_bold_entity_blocks(b))
                    else:
                        raw_entity_blocks.append(b)

            # Step C: For each detected entity block, assemble context and chunk adaptively
            for entity_text in raw_entity_blocks:
                # Faculty Metadata Resolution
                if category == "faculty" and faculty_name:
                    section_faculty = [faculty_name]
                    INGESTION_METRICS["faculty_chunks"] += 1
                else:
                    extracted_fac = extract_faculty_from_text(entity_text)
                    merged_fac = []
                    if fm_faculty_name:
                        if isinstance(fm_faculty_name, list):
                            merged_fac.extend(fm_faculty_name)
                        else:
                            merged_fac.append(fm_faculty_name)
                    merged_fac.extend(extracted_fac)
                    section_faculty = _normalize_metadata_value(merged_fac)
                    if isinstance(section_faculty, str):
                        section_faculty = [section_faculty]
                    elif section_faculty is None:
                        section_faculty = []

                # Course Code Resolution (Document-Type Aware)
                if is_single_course_doc and fm_course_code:
                    # Trust Frontmatter ONLY for single-course documents (prevent pollution from body text)
                    section_course_codes = _normalize_metadata_value(fm_course_code)
                else:
                    # Merge section-local codes for multi-course documents (curriculum, timetables)
                    extracted_codes = extract_course_codes_from_text(entity_text)
                    merged_codes = []
                    if fm_course_code:
                        if isinstance(fm_course_code, list):
                            merged_codes.extend(fm_course_code)
                        else:
                            merged_codes.append(fm_course_code)
                    merged_codes.extend(extracted_codes)
                    section_course_codes = _normalize_metadata_value(merged_codes)

                if isinstance(section_course_codes, str):
                    section_course_codes = [section_course_codes]
                elif section_course_codes is None:
                    section_course_codes = []

                if section_course_codes:
                    INGESTION_METRICS["course_chunks"] += 1

                # Build preserved self-contained heading context
                context_prefix = ""
                if section_faculty:
                    context_prefix += f"Faculty Name: {', '.join(section_faculty)}\n\n"

                if category == "doctoral scholars" and metadata.get("title"):
                    context_prefix += f"Document Title: {metadata.get('title')}\n"

                if section["h1"]:
                    context_prefix += f"H1: {section['h1']}\n"
                if section["h2"]:
                    context_prefix += f"H2: {section['h2']}\n"
                if effective_h3:
                    context_prefix += f"H3: {effective_h3}\n"
                if effective_h4:
                    context_prefix += f"H4: {effective_h4}\n"

                contextualized_entity = (context_prefix + "\n" + entity_text).strip()

                # Step D: Adaptive Chunking (1 entity <= 256 tokens -> 1 chunk, else semantic split)
                split_chunks = _adaptive_split_entity(contextualized_entity, max_tokens=256)

                # Track entity counts
                if "club" in relative_path.lower() or "club" in (metadata.get("title") or "").lower():
                    INGESTION_METRICS["club_chunks"] += len(split_chunks)
                if "committee" in relative_path.lower() or "sbg" in relative_path.lower():
                    INGESTION_METRICS["committee_chunks"] += len(split_chunks)

                for chunk_text in split_chunks:
                    start_line, end_line = find_line_range_in_file(
                        chunk_text,
                        file_lines,
                        section_start=section["start_line"],
                        section_end=section["end_line"]
                    )
                    section_header_key = section.get("h1") or section.get("h2") or effective_h3 or ""
                    chunk_id = generate_deterministic_chunk_id(
                        relative_path=relative_path,
                        chunk_text=chunk_text,
                        section_key=section_header_key
                    )

                    token_est = len(chunk_text.split())
                    INGESTION_METRICS["chunks_generated"] += 1
                    INGESTION_METRICS["total_characters"] += len(chunk_text)
                    INGESTION_METRICS["total_tokens"] += token_est
                    if token_est > INGESTION_METRICS["max_chunk_tokens"]:
                        INGESTION_METRICS["max_chunk_tokens"] = token_est

                    chunk_record = {
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "title": metadata.get("title"),
                        "url": metadata.get("url"),
                        "category": metadata.get("category"),
                        "document_type": category,
                        "cluster": cluster,
                        "subclusters": subclusters,
                        "h1": section["h1"],
                        "h2": section["h2"],
                        "h3": effective_h3,
                        "section_type": section_type,
                        "path": str(file_path),
                        "source_file": file_path.name,
                        "relative_path": relative_path,
                        "scraped_date": metadata.get("scraped_date"),
                        "authorization": authorization,
                        "char_length": len(chunk_text),
                        "token_estimate": token_est,
                        "start_line": start_line,
                        "end_line": end_line,
                        "document_year": document_year,
                    }
                    if academic_year:
                        chunk_record["academic_year"] = academic_year
                    chunk_record.update(academic_applicability)

                    if section_faculty:
                        chunk_record["faculty_name"] = section_faculty if len(section_faculty) > 1 else section_faculty[0]
                    if section_course_codes:
                        chunk_record["course_code"] = section_course_codes if len(section_course_codes) > 1 else section_course_codes[0]

                    target_semester = effective_semester or metadata.get("semester")
                    if target_semester:
                        chunk_record["semester"] = target_semester

                    if effective_program_name:
                        chunk_record["program_name"] = effective_program_name

                    target_event = event_metadata.get("event_name") or fm_event_name
                    if target_event:
                        chunk_record["event_name"] = target_event

                    if event_metadata:
                        chunk_record.update({k: v for k, v in event_metadata.items() if k != "event_name"})

                    chunks.append(chunk_record)

    # Add custom curriculum chunks (Preserved intact)
    curriculum_chunks = extract_curriculum_chunks(body, metadata, file_path)
    for custom in curriculum_chunks:
        start_line, end_line = find_line_range_in_file(
            custom["text"],
            file_lines,
            section_start=frontmatter_offset + 1,
            section_end=len(file_lines)
        )
        custom_header_key = custom.get("h1") or custom.get("h2") or ""
        custom_chunk_id = generate_deterministic_chunk_id(
            relative_path=relative_path,
            chunk_text=custom["text"],
            section_key=custom_header_key
        )
        token_est = len(custom["text"].split())
        INGESTION_METRICS["chunks_generated"] += 1
        INGESTION_METRICS["total_characters"] += len(custom["text"])
        INGESTION_METRICS["total_tokens"] += token_est

        chunk_record = {
            "chunk_id": custom_chunk_id,
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
            "relative_path": relative_path,
            "scraped_date": metadata.get("scraped_date"),
            "authorization": authorization,
            "char_length": len(custom["text"]),
            "token_estimate": token_est,
            "start_line": start_line,
            "end_line": end_line,
            "document_year": document_year,
        }
        if academic_year:
            chunk_record["academic_year"] = academic_year
        chunk_record.update(academic_applicability)

        if effective_program_name:
            chunk_record["program_name"] = effective_program_name
            
        chunk_record["semester"] = _normalize_metadata_value(custom.get("semester") or effective_semester)
        chunk_record["course_code"] = _normalize_metadata_value(custom.get("course_code") or fm_course_code)
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

    return chunks
