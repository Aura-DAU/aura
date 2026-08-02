"""
generate_timetables.py — parses the official DAU Autumn 2026-27 timetable
PDF (grid-structured, via pdfplumber) into one markdown table per cohort
(year+section for BTech, branch for BS-MS/MSc, etc.), and writes them to
data/academics/timetable/.

Why this exists instead of using pipeline/timetable/xlsx_parser.py:
xlsx_parser.py expects a real .xlsx workbook with a specific column
layout (openpyxl cell references) — there is no .xlsx in this project,
only this PDF. This script works directly off the PDF's actual table
grid (extracted via pdfplumber, which respects real column boundaries),
rather than a flattened/linearized text dump, which is what was silently
producing garbage before (day columns and rows getting concatenated with
no reliable boundaries to split on).

Per the request: elective slots are appended to EVERY cohort's file
(not filtered to "selected" electives), since electives are pooled
across an entire year/semester rather than being section-specific.
"""

import pdfplumber
import re
import json
from pathlib import Path
from collections import defaultdict

PDF_PATH = "/mnt/user-data/uploads/Draft_TT_Autumn2026-27_v6.pdf"
OUT_DIR = Path("data/academics/timetable")
TIMETABLE_PAGES = 4  # pages 0-3 are the grid; 4+ is the faculty-initials legend

DAY_COLS = {
    "Monday": (3, 4, 5), "Tuesday": (6, 7, 8), "Wednesday": (9, 10, 11),
    "Thursday": (12, 13, 14), "Friday": (15, 16, 17),
}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Exact mapping from every distinct batch string actually observed in the
# PDF (verified against data/academics/timetable/_raw_records.json) to a
# canonical cohort name. A few of these are OCR/export artifacts in the
# source PDF itself, not parsing bugs — e.g. "Btech 3r Yr" is genuinely
# missing the 'd' in the source document, and "Btech2ndYr" (no spaces) is
# a second, differently-formatted occurrence of the same batch later in
# the document.
BATCH_MAP = {
    "Btech 1st Yr": "Btech 1st Yr",
    "Btech 2nd Yr": "Btech 2nd Yr",
    "Btech 2nd Year": "Btech 2nd Yr",
    "Btech2ndYr": "Btech 2nd Yr",
    "Btech 3rd Yr": "Btech 3rd Yr",
    "Btech 3r Yr": "Btech 3rd Yr",           # source PDF typo (missing 'd')
    "tech 3rd Yr (Core": "Btech 3rd Yr",     # source PDF: leading 'B' clipped by the table's cell boundary
    "BS-MS (IT)": "BS-MS (IT)",
    "BS-MS (DS + AI)": "BS-MS (DS + AI)",
    "Mtech (Core)": "Mtech (Core)",
    "MSc (AA)": "MSc (AA)",
    "MSC (AA)": "MSc (AA)",
    "MSc(AA)": "MSc (AA)",
    "MSc (DS) Core": "MSc DS (Core)",        # word-order variant, same cohort
    "MSc DS (Core)": "MSc DS (Core)",
    "MSc (IT) Core": "MSc IT (Core)",
    "Elective": "Elective",
    # "Btech Core" (CS374 at the 5pm slot) doesn't state which year it's
    # for anywhere in the source PDF — kept as its own clearly-flagged
    # cohort rather than guessed into a specific year.
    "Btech Core": "Btech Core (year unspecified in source — verify manually)",
}

BTECH_SECTIONED_PREFIXES = ("Btech 1st Yr", "Btech 2nd Yr", "Btech 3rd Yr")

CODE_SECTION_RE = re.compile(r"\s*\(\s*([A-Z0-9])\s*\)\s*$", re.IGNORECASE)


def normalize_batch(raw: str) -> str:
    raw = raw.strip()
    if raw in BATCH_MAP:
        return BATCH_MAP[raw]
    # Fallback for anything not seen during development: strip all
    # non-alphanumerics and compare loosely, so small future formatting
    # drift (extra spaces, case) doesn't silently create a duplicate file.
    norm = re.sub(r"[^a-z0-9]", "", raw.lower())
    for known_raw, canonical in BATCH_MAP.items():
        if re.sub(r"[^a-z0-9]", "", known_raw.lower()) == norm:
            return canonical
    return raw


def decode_time_cell(cell) -> str | None:
    """The time-slot cells render as vertically-mirrored text in this
    PDF's export (e.g. '05:8\\n-\\n00:8' for '8:00 - 8:50') — reversing
    the whole string (including newlines) un-mirrors it correctly."""
    if not cell or not cell.strip():
        return None
    s = cell[::-1].replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if not re.match(r"^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", s):
        return None
    return s


def extract_section(code_raw: str) -> tuple[str, str | None]:
    m = CODE_SECTION_RE.search(code_raw)
    if m:
        return code_raw[: m.start()].strip(), m.group(1).upper()
    return code_raw.strip(), None


def is_header_or_title_row(row) -> bool:
    c0 = (row[0] or "").strip()
    c3 = (row[3] or "").strip() if len(row) > 3 else ""
    if c0 in ("Dhirubhai Ambani University",) or c0.startswith("Lecture Time-Table"):
        return True
    if c3 in ("Course", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        return True
    return False


def extract_all_rows() -> list[list]:
    rows_all = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for pi in range(min(TIMETABLE_PAGES, len(pdf.pages))):
            table = pdf.pages[pi].extract_table()
            if table:
                rows_all.extend(table)
    return rows_all


def parse_records() -> list[dict]:
    rows = extract_all_rows()
    records = []
    dropped_orphan_rows = 0
    current_time = None
    current_batch_raw = None

    for row in rows:
        c0 = (row[0] or "").strip() if len(row) > 0 else ""
        if c0 == "Dhirubhai Ambani University" or c0.startswith("Lecture Time-Table"):
            # Page boundary. A batch label is sometimes split from its own
            # data across the page break (label ends up on one side, data
            # on the other, with no label repeated on the data's side) —
            # carrying the pre-break batch forward would silently
            # misattribute that data to the wrong cohort. Safer to require
            # a fresh, unambiguous batch label after every page break and
            # drop anything that shows up without one.
            current_batch_raw = None
            continue

        if is_header_or_title_row(row):
            continue

        t = decode_time_cell(row[0] if len(row) > 0 else None)
        if t:
            current_time = t

        batch_cell = (row[2] or "").strip() if len(row) > 2 else ""
        if batch_cell:
            current_batch_raw = batch_cell

        if not current_time or not current_batch_raw:
            if current_time and any((row[c] or "").strip() for cols in DAY_COLS.values() for c in cols[:1]):
                dropped_orphan_rows += 1
            continue

        batch = normalize_batch(current_batch_raw)
        start, end = [x.strip() for x in current_time.split("-", 1)]

        for day in DAY_ORDER:
            code_col, fac_col, room_col = DAY_COLS[day]
            code_raw = (row[code_col] or "").strip() if len(row) > code_col else ""
            if not code_raw or code_raw == ".":
                continue
            faculty = (row[fac_col] or "").strip() if len(row) > fac_col else ""
            room = (row[room_col] or "").strip() if len(row) > room_col else ""
            code, section = extract_section(code_raw)

            # Confirmed page artifact: a few MSc DS Core rows sometimes
            # appear with no label of their own while "MSc IT (Core)" is
            # still the active batch (verified against row 223 of the
            # extracted grid — DS6xx codes inherited the wrong cohort).
            # Course-code prefix is a reliable enough signal to correct
            # this specific, confirmed mixup rather than mislabeling it.
            row_batch = batch
            if row_batch == "MSc IT (Core)" and code.startswith("DS"):
                row_batch = "MSc DS (Core)"
            elif row_batch == "MSc DS (Core)" and code.startswith("IT"):
                row_batch = "MSc IT (Core)"

            records.append({
                "batch": row_batch, "day": day, "start": start, "end": end,
                "course_code": code, "section": section,
                "faculty": faculty, "room": room,
                "is_elective": row_batch == "Elective",
            })

    if dropped_orphan_rows:
        print(f"NOTE: dropped {dropped_orphan_rows} row(s) with class data but no identifiable "
              f"batch (page-break artifacts) — see script docstring.")

    return records


def build_cohorts(records: list[dict]) -> dict[str, list[dict]]:
    """Groups records into one list per output file.

    BTech cohorts are split per section, but a class listed with no
    section attached (e.g. a shared core lecture all sections attend
    together) applies to every section of that year — so it's
    replicated into each section's list rather than becoming an
    orphaned "no section" file of its own.
    """
    non_elective = [r for r in records if not r["is_elective"]]

    sections_by_batch: dict[str, set[str]] = defaultdict(set)
    for r in non_elective:
        if r["batch"] in BTECH_SECTIONED_PREFIXES and r["section"]:
            sections_by_batch[r["batch"]].add(r["section"])

    by_cohort: dict[str, list[dict]] = defaultdict(list)
    for r in non_elective:
        if r["batch"] in BTECH_SECTIONED_PREFIXES:
            known_sections = sorted(sections_by_batch.get(r["batch"], []))
            if r["section"]:
                by_cohort[f"{r['batch']} Section {r['section']}"].append(r)
            elif known_sections:
                # Common class with no section marked — every section attends.
                for sec in known_sections:
                    by_cohort[f"{r['batch']} Section {sec}"].append(r)
            else:
                by_cohort[r["batch"]].append(r)
            # Also keep a combined "whole year" view.
            by_cohort[f"{r['batch']} (All Sections Combined)"].append(r)
        else:
            by_cohort[r["batch"]].append(r)

    return by_cohort


def render_markdown(cohort_name: str, own_records: list[dict], elective_records: list[dict]) -> str:
    lines = [f"# Timetable — {cohort_name} (Autumn 2026-27)", ""]
    lines.append("Source: official DAU Autumn 2026-27 lecture timetable.")
    lines.append("")

    def table(records, heading):
        out = [f"## {heading}", "", "| Day | Time | Course | Faculty | Room |", "|---|---|---|---|---|"]
        by_day = defaultdict(list)
        for r in records:
            by_day[r["day"]].append(r)
        for day in DAY_ORDER:
            for r in sorted(by_day[day], key=lambda x: x["start"]):
                course = r["course_code"] + (f" (Sec {r['section']})" if r["section"] else "")
                out.append(f"| {day} | {r['start']}-{r['end']} | {course} | {r['faculty']} | {r['room']} |")
        if len(out) == 5:
            out.append("| — | — | *No classes found* | — | — |")
        out.append("")
        return out

    lines += table(own_records, "Core schedule")
    lines += table(elective_records, "Electives (open to all sections/years — check availability before selecting)")
    return "\n".join(lines)


def main():
    records = parse_records()
    elective_records = [r for r in records if r["is_elective"]]
    by_cohort = build_cohorts(records)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for cohort_name, recs in sorted(by_cohort.items()):
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", cohort_name).strip("_")
        path = OUT_DIR / f"{slug}.md"
        path.write_text(render_markdown(cohort_name, recs, elective_records), encoding="utf-8")
        written.append((cohort_name, path, len(recs)))

    # Also a standalone electives reference file
    elec_path = OUT_DIR / "Electives_All.md"
    elec_path.write_text(
        render_markdown("All Electives (Autumn 2026-27)", [], elective_records), encoding="utf-8"
    )
    written.append(("Electives (standalone)", elec_path, len(elective_records)))

    print(f"Parsed {len(records)} total slot records ({len(elective_records)} elective).")
    print(f"Wrote {len(written)} files to {OUT_DIR}/:")
    for name, path, n in written:
        print(f"  {path.name:40s}  {n:3d} records  ({name})")

    with open(OUT_DIR / "_raw_records.json", "w") as f:
        json.dump(records, f, indent=2)


if __name__ == "__main__":
    main()
