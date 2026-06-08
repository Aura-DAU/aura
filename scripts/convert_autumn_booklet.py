"""
Autumn 2025 Course Booklet Converter (Page-number-based)
=========================================================
Uses the page numbers embedded in existing autumn_2025 filenames as
ground truth to know exactly where each course starts in the PDF.
Then re-extracts each course section with proper table support.
"""

import re
import json
import datetime
import pdfplumber
from pathlib import Path

PDF_PATH   = Path(r"C:\Users\ADMIN\Downloads\Course Booklet for Autumn 2025-26.pdf")
OUTPUT_DIR = Path(r"C:\Users\ADMIN\Downloads\DAU-pwa-main (1)\DAU-pwa-main\data\academics")

SCRAPED_DATE = datetime.date.today().isoformat()
BASE_URL     = "https://intranet.daiict.ac.in/academics/Course_Booklet_for_Autumn_2025-26.pdf"
PDF_NAME     = "Course_Booklet_for_Autumn_2025-26.pdf"

# ─── Table / Text Extraction ──────────────────────────────────────────────────

def clean_cell(c) -> str:
    return str(c or "").replace("\n", " ").replace("|", "\\|").strip()


def table_to_markdown(table: list) -> str:
    if not table or not any(any(c for c in row) for row in table):
        return ""
    col_count = max(len(row) for row in table)
    padded = [list(row) + [""] * (col_count - len(row)) for row in table]
    header = padded[0]
    lines = []
    lines.append("| " + " | ".join(clean_cell(c) for c in header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in padded[1:]:
        lines.append("| " + " | ".join(clean_cell(c) for c in row) + " |")
    return "\n".join(lines)


def extract_page_content(page) -> str:
    """Extract page content preserving tables as proper markdown."""
    try:
        tables = page.find_tables()
    except Exception:
        tables = []

    if not tables:
        try:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            return text.strip() if text else ""
        except Exception:
            return ""

    table_bboxes = [t.bbox for t in tables]

    rendered_tables = []
    for t in tables:
        try:
            data = t.extract()
            md = table_to_markdown(data)
            if md:
                rendered_tables.append({"bbox": t.bbox, "md": md, "y": t.bbox[1]})
        except Exception:
            pass

    # Words outside tables
    try:
        words = page.extract_words(x_tolerance=3, y_tolerance=3)
    except Exception:
        words = []

    non_table_words = []
    for word in words:
        wx0, wy0, wx1, wy1 = word["x0"], word["top"], word["x1"], word["bottom"]
        in_table = any(
            wx0 >= tx0 - 5 and wx1 <= tx1 + 5 and wy0 >= ty0 - 5 and wy1 <= ty1 + 5
            for tx0, ty0, tx1, ty1 in table_bboxes
        )
        if not in_table:
            non_table_words.append(word)

    text_blocks = []
    if non_table_words:
        line_groups: dict[int, list] = {}
        for w in non_table_words:
            y_key = round(w["top"] / 4) * 4
            line_groups.setdefault(y_key, []).append(w)

        lines_sorted = []
        for y in sorted(line_groups.keys()):
            lw = sorted(line_groups[y], key=lambda w: w["x0"])
            lines_sorted.append((
                sum(w["top"] for w in lw) / len(lw),
                " ".join(w["text"] for w in lw)
            ))

        if lines_sorted:
            cur_lines = [lines_sorted[0][1]]
            cur_y = lines_sorted[0][0]
            for y, line in lines_sorted[1:]:
                if y - cur_y > 20:
                    text_blocks.append((cur_y, "\n".join(cur_lines)))
                    cur_lines = [line]
                else:
                    cur_lines.append(line)
                cur_y = y
            if cur_lines:
                text_blocks.append((cur_y, "\n".join(cur_lines)))

    all_items = [(y, txt.strip()) for y, txt in text_blocks if txt.strip()]
    for t in rendered_tables:
        all_items.append((t["y"], "\n" + t["md"] + "\n"))
    all_items.sort(key=lambda x: x[0])
    return "\n\n".join(item[1] for item in all_items)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"_+", "_", text)
    return text[:100]


def infer_course_code(text: str) -> str:
    m = re.search(r"\b([A-Z]{2,4}\s*(?:\d|X){3,4}[A-Z]?)\b", text, re.IGNORECASE)
    return re.sub(r"\s+", "", m.group(1)).upper() if m else ""


def clean_line(line: str, code: str) -> str:
    cleaned = line
    cleaned = re.sub(r"\(\s*\d\s*-\s*\d\s*-\s*\d\s*-\s*\d\s*\)", "", cleaned)
    cleaned = re.sub(r"\(\s*\d\s*-\s*\d\s*-\s*\d\s*\)", "", cleaned)
    cleaned = re.sub(r"\(\s*(?:autumn|spring|semester|credits|ug|pg|core|elective)[^)]*\)", "", cleaned, flags=re.IGNORECASE)
    
    if code:
        code_pat = r"\b" + r"\s*".join(code) + r"\b"
        cleaned = re.sub(code_pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[A-Z]{2,4}\s*(?:\d|X){3,4}[A-Z]?\b", "", cleaned, flags=re.IGNORECASE)
    
    junk = [
        "course file", "da-iict", "gandhinagar", "dhirubhai ambani",
        "course handout", "course outline", "evaluation policy",
        "general course information", "course information", "programme:",
        "academic year:", "semester:", "course placement:", "title:"
    ]
    for j in junk:
        cleaned = re.sub(r"\b" + re.escape(j) + r"\b", "", cleaned, flags=re.IGNORECASE)
        
    cleaned = re.sub(r"^(?:elective|core|technical|open|science)\s+course\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned)
    cleaned = re.sub(r"^\d+\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def infer_title(text: str, code: str) -> str:
    """Extract course title from page text."""
    # Pattern: "Course Title: <value>" or "Title of Course: <value>"
    patterns = [
        r"(?:Course\s+Title|Title\s+of\s+Course)\s*[:\|]?\s*\n?\s*([^\n|]{3,80})",
        r"(?:Course\s+Name)\s*[:\|]?\s*\n?\s*([^\n|]{3,80})",
        # Table cell after course code in header row
        r"\|\s*(?:Course\s+Title|Title\s+of\s+Course)\s*\|\s*([^|\n]{3,80})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            t = m.group(1).strip().rstrip("|").strip()
            if 3 < len(t) < 100 and not re.match(r"^\d", t):
                return t
                
    # Heuristics with line joining
    lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
    for idx, line in enumerate(lines):
        if any(x in line.lower() for x in ["institute of", "dhirubhai ambani", "da-iict", "gandhinagar"]):
            continue
            
        cleaned = clean_line(line, code)
        
        if 3 <= len(cleaned) <= 80:
            if not any(x in cleaned.lower() for x in ["syllabus", "lecture plan", "grading policy", "evaluation scheme"]):
                # Join with next line if ends in coordinating word
                if cleaned.lower().endswith(("and", "or", "of", "for", "with", "in", "to", "the", "a", "an", "-", "&", ",")) and idx + 1 < len(lines):
                    next_cleaned = clean_line(lines[idx + 1], code)
                    if next_cleaned:
                        cleaned = cleaned + " " + next_cleaned
                return cleaned
                
    return "Unknown Course"


def build_markdown(course_code: str, title: str, content: str,
                    start_page: int, end_page: int, orig_filename: str) -> str:
    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    frontmatter = f"""---
title: "{title}"
url: "{BASE_URL}"
category: "Academics - Course Policies"
scraped_by: "Squad D Scraper"
scraped_date: "{SCRAPED_DATE}"
team: "Squad D"
source_type: "PDF"
pdf_name: "{PDF_NAME}"
course_code: "{course_code}"
semester: "Autumn 2025-26"
pdf_page_start: {start_page}
pdf_page_end: {end_page}
---"""

    footer = f"""
## Important Information

- **Course Code:** {course_code}
- **Course Title:** {title}
- **Document Source:** {PDF_NAME} (pages {start_page}–{end_page})
- **Semester:** Autumn 2025-26
- **Scraped At:** {now_utc} UTC

## Related Links

- [DA-IICT Intranet Portal](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp)
- [Academic Guidelines](https://daiict.ac.in/academics)

## Downloadable Resources

| Resource | Type | Link |
|---|---|---|
| {PDF_NAME} | PDF | [Download {PDF_NAME}]({BASE_URL}) |
"""

    return f"""{frontmatter}

# {title} ({course_code})

## Main Content

{content.strip()}
{footer}"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Autumn 2025 Course Booklet -> Markdown (Page-number mode)")
    print("=" * 65)

    # ── Step 1: Read page numbers from existing filenames ────────────────
    # Pattern: course_policy_<slug>_autumn_2025_page_<N>.md
    existing = sorted(OUTPUT_DIR.glob("course_policy_*autumn_2025*page_*.md"))
    print(f"Found {len(existing)} existing autumn_2025 files with page info")

    # Build sorted list of (page_1idx, original_filename)
    page_files = []
    for f in existing:
        m = re.search(r"_page_(\d+)\.md$", f.name)
        if m:
            pg = int(m.group(1))
            page_files.append((pg, f))

    # Deduplicate: if two files have same page, keep one
    seen_pages = {}
    for pg, f in page_files:
        if pg not in seen_pages:
            seen_pages[pg] = f
        # Keep the file with longer slug (more descriptive)
        elif len(f.name) > len(seen_pages[pg].name):
            seen_pages[pg] = f

    page_files = sorted(seen_pages.items())  # [(page, file), ...]
    print(f"Unique start pages: {len(page_files)}")
    print(f"Page range: {page_files[0][0]} to {page_files[-1][0]}")

    # ── Step 2: Delete all old autumn_2025 files ─────────────────────────
    all_autumn = list(OUTPUT_DIR.glob("course_policy_*autumn_2025*.md"))
    print(f"\nDeleting {len(all_autumn)} old autumn_2025 files...", end="", flush=True)
    for f in all_autumn:
        f.unlink()
    print(" done")

    # ── Step 3: Convert each course section ──────────────────────────────
    ok = failed = 0

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF total pages: {total_pages}\n")

        for i, (start_pg_1, orig_file) in enumerate(page_files):
            # start_pg_1 from filename is actually 0-indexed index
            start_0 = start_pg_1
            
            # Determine end page (start of next course)
            if i + 1 < len(page_files):
                end_0 = page_files[i + 1][0]
            else:
                end_0 = total_pages

            # Cap to valid range
            start_0 = max(0, min(start_0, total_pages - 1))
            end_0   = max(start_0 + 1, min(end_0, total_pages))

            page_count = end_0 - start_0
            start_display = start_0 + 1
            end_display   = end_0
            print(f"[{i+1:03d}/{len(page_files)}] p{start_display}–{end_display} ({page_count} pages) orig: {orig_file.name[:60]}", end="", flush=True)

            # Extract all pages
            page_contents = []
            for pg_idx in range(start_0, end_0):
                try:
                    content = extract_page_content(pdf.pages[pg_idx])
                    if content.strip():
                        page_contents.append(content)
                except Exception as e:
                    pass  # skip bad pages silently

            if not page_contents:
                print(" -> NO CONTENT")
                failed += 1
                continue

            full_content = "\n\n---\n*Page Split*\n---\n\n".join(page_contents)

            # Infer course code and title from content
            code  = infer_course_code(full_content[:1500]) or infer_course_code(orig_file.name)
            title = infer_title(full_content[:2000], code)
            
            code = code or "unknown"

            # Build output filename, preserving page number for reference
            if code == "unknown" or title == "Unknown Course":
                clean_orig_stem = (orig_file.stem
                                    .replace("course_policy_", "")
                                    .replace(f"_autumn_2025_page_{start_pg_1}", "")
                                    .replace("__unknown", "")
                                    .replace("_unknown", "")
                                    .strip("_"))
                title_slug = slugify(title) if title != "Unknown Course" else slugify(clean_orig_stem)
            else:
                title_slug = slugify(title)
                
            code_lower = code.lower()
            md_name = f"course_policy_{code_lower}_{title_slug}_autumn_2025_page_{start_pg_1}.md"
            out_path = OUTPUT_DIR / md_name

            md_doc = build_markdown(code, title, full_content, start_display, end_display, orig_file.name)
            out_path.write_text(md_doc, encoding="utf-8")

            size_kb = len(md_doc) // 1024
            print(f" -> {size_kb} KB")
            ok += 1

    print(f"\n{'='*65}")
    print(f"DONE: {ok} converted, {failed} failed")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
