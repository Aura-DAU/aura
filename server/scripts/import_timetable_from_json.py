#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_timetable_from_json.py
Imports data/academics/timetable/_raw_records.json into PostgreSQL timetable_master.

Usage (from repo root):
    python server/scripts/import_timetable_from_json.py --dry-run
    python server/scripts/import_timetable_from_json.py --clear
"""
import argparse, json, os, re, sys
from pathlib import Path
from collections import Counter

REPO_ROOT  = Path(__file__).resolve().parent.parent.parent
SERVER_DIR = REPO_ROOT / "server"
DATA_DIR   = REPO_ROOT / "data" / "academics" / "timetable"
JSON_FILE  = DATA_DIR / "_raw_records.json"
ENV_FILE   = SERVER_DIR / ".env"
sys.path.insert(0, str(SERVER_DIR))

# Autumn 2026-27 = odd semesters: Yr1->Sem1, Yr2->Sem3, Yr3->Sem5
BATCH_MAP = {
    "Btech 1st Yr":    ("BTech",  1, 1, ""),
    "Btech 2nd Yr":    ("BTech",  2, 3, ""),
    "Btech 3rd Yr":    ("BTech",  3, 5, ""),
    "Elective":        ("All",    0, 0, "Elective"),
    "MSc (AA)":        ("MSc",    1, 1, "AA"),
    "MSc DS (Core)":   ("MSc",    1, 1, "DS"),
    "MSc IT (Core)":   ("MSc",    1, 1, "IT"),
    "Mtech (Core)":    ("MTech",  1, 1, "Core"),
    "BS-MS (DS + AI)": ("BS-MS",  1, 1, "DS+AI"),
    "BS-MS (IT)":      ("BS-MS",  1, 1, "IT"),
}
DAY_MAP = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,
           "Friday":4,"Saturday":5,"Sunday":6}


def norm_time(t):
    t = (t or "").strip().lower()
    is_pm = "pm" in t
    is_am = "am" in t
    t = t.replace("am", "").replace("pm", "").strip()
    p = t.split(":")
    if len(p) == 2:
        try:
            hr = int(p[0])
            if is_pm and hr != 12:
                hr += 12
            elif is_am and hr == 12:
                hr = 0
            elif not is_pm and not is_am:
                # DAU classes heuristic: 8:00 to 19:00.
                if 1 <= hr <= 7:
                    hr += 12
            return "{:02d}:{:02d}".format(hr, int(p[1]))
        except ValueError:
            pass
    return t


def guess_session(cc, cn):
    s = (cc + " " + cn).lower()
    if "lab" in s: return "lab"
    if "tutorial" in s: return "tutorial"
    return "lecture"


def guess_ctype(is_el, cc):
    if is_el: return "Elective"
    m = re.match(r"^[A-Za-z]+", cc)
    p = m.group(0).upper() if m else ""
    return {"IC": "Institute Core", "PC": "Program Core",
            "HM": "Humanities"}.get(p, "Core")


def parse_names():
    """Extract course_code -> course_name from markdown files."""
    names = {}
    # Matches table cells like:  IC101 (Sec A) — Introduction to ICT
    # em-dash \u2014, en-dash \u2013, or ASCII hyphen are all accepted
    pat = re.compile(
        r"\|\s*([A-Z]{1,5}\d{2,4})\s*(?:\([^)]*\)\s*)?[\u2014\u2013\-]+\s*([^|\n]+)",
        re.IGNORECASE,
    )
    for f in DATA_DIR.glob("*.md"):
        for m in pat.finditer(f.read_text(encoding="utf-8", errors="replace")):
            code = m.group(1).upper().strip()
            name = m.group(2).strip().rstrip("|").strip()
            if name and (code not in names or len(name) > len(names[code])):
                names[code] = name
    return names


def main():
    ap = argparse.ArgumentParser(description="Import timetable JSON to PostgreSQL")
    ap.add_argument("--dry-run", action="store_true", help="Preview, no DB changes")
    ap.add_argument("--clear",   action="store_true", help="DELETE existing rows first")
    ap.add_argument("--semester", default="Autumn 2026-27")
    ap.add_argument("--db-url",  default=None)
    args = ap.parse_args()

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if args.db_url:
        os.environ["AUTH_DB_URL"] = args.db_url

    if not JSON_FILE.exists():
        sys.exit("ERROR: not found: {}".format(JSON_FILE))

    records = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    print("[INFO ] {} records loaded".format(len(records)))

    cnames = parse_names()
    print("[INFO ] {} course names from markdown".format(len(cnames)))

    rows, skipped = [], []
    for i, r in enumerate(records):
        batch = (r.get("batch") or "").strip()
        if "Btech Core" in batch:
            skipped.append((i, "year-unspecified Btech Core - skip"))
            continue
        if batch not in BATCH_MAP:
            skipped.append((i, "unknown batch: {!r}".format(batch)))
            continue
        program, year, sem, branch = BATCH_MAP[batch]

        dow = DAY_MAP.get(r.get("day", ""))
        if dow is None:
            skipped.append((i, "unknown day: {!r}".format(r.get("day"))))
            continue

        cc = (r.get("course_code") or "").strip().upper()
        if not cc:
            skipped.append((i, "missing course_code"))
            continue

        sec  = (r.get("section") or "").strip().upper()  # '' = common to all sections
        st   = norm_time(r.get("start", "")) or None
        et   = norm_time(r.get("end",   "")) or None
        fac  = (r.get("faculty") or "").strip() or None
        room = (r.get("room")    or "").strip() or None
        isel = bool(r.get("is_elective", False))
        cn   = cnames.get(cc, cc)

        rows.append((year, sem, sec, dow, st, et, cc, cn,
                     guess_session(cc, cn), room, fac,
                     guess_ctype(isel, cc), program, batch, branch or None, None))

    print("[INFO ] {} rows ready, {} skipped".format(len(rows), len(skipped)))
    for s in skipped[:10]:
        print("  skip:", s)
    if len(skipped) > 10:
        print("  ... and {} more".format(len(skipped) - 10))

    dist = Counter((r[0], r[1], r[2], r[12]) for r in rows)
    print("\n  (year,sem,sec,program) -> count")
    for k, v in sorted(dist.items()):
        print("   ", k, "->", v)

    if args.dry_run:
        print("\n[DRY-RUN] No DB changes. Remove --dry-run to import.")
        return

    import db.connection as dbc

    if args.clear:
        pairs = sorted(set((r[0], r[1]) for r in rows))
        print("\n[CLEAR] Deleting for (year,sem):", pairs)
        for yr, sm in pairs:
            dbc.execute("DELETE FROM timetable_master WHERE year=%s AND sem=%s AND (lab_group IS NULL AND (session_type IS NULL OR session_type NOT IN ('lab', 'tutorial')))", (yr, sm))
        print("[CLEAR] Done.")

    SQL = (
        "INSERT INTO timetable_master "
        "(year,sem,sec,day_of_week,start_time,end_time,"
        "course_code,course_name,session_type,room,faculty_name,"
        "course_type,program,batch_raw,branch,credits) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )
    ok = err = 0
    for row in rows:
        try:
            dbc.execute(SQL, row)
            ok += 1
        except Exception as e:
            err += 1
            if err <= 5:
                print("[ERR  ] {} | {}".format(e, row[:6]))

    print("\n[DONE ] Inserted {}/{} rows. Errors: {}".format(ok, len(rows), err))
    print("\n[VERIFY] timetable_master counts:")
    for c in dbc.query(
        "SELECT year,sem,sec,program,COUNT(*) n FROM timetable_master "
        "GROUP BY year,sem,sec,program ORDER BY program,year,sem,sec"
    ):
        print("  Yr{yr} Sem{sem} Sec{sec!r:5} {prog:9} -> {n}".format(
            yr=c["year"], sem=c["sem"], sec=c["sec"],
            prog=c["program"], n=c["n"]))


if __name__ == "__main__":
    main()
