#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from collections import Counter
import argparse

SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_DIR))
DATA_DIR = SERVER_DIR.parent / "data" / "academics" / "lab"

DAY_MAP = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}

def parse_filename(filename):
    """
    Extracts program, year, sem, branch, lab_group from filename.
    Example: CS-AI_1st_Yr_Lab_G1.md -> branch='CS-AI', year=1, sem=1, lab_group='G1'
    EVD_2nd_Yr_Sem3_Lab.md -> branch='EVD', year=2, sem=3, lab_group=None
    """
    name = filename.replace(".md", "")
    lab_group = None
    if "_G" in name:
        parts = name.split("_G")
        lab_group = "G" + parts[1]
        name = parts[0]
    
    # Defaults
    program = "BTech"
    if "MSc_" in name or "Mtech_" in name or "BS_MS_" in name:
        if "MSc_" in name: 
            program = "MSc"
            name = name.replace("MSc_", "")
        elif "Mtech_" in name: 
            program = "MTech"
            name = name.replace("Mtech_", "")
        elif "BS_MS_" in name: 
            program = "BS-MS"
            name = name.replace("BS_MS_", "")
    
    year = 1
    sem = 1
    if "1st_Yr" in name: year = 1; sem = 1
    elif "2nd_Yr_Sem3" in name: year = 2; sem = 3
    elif "3rd_Yr_Sem5" in name: year = 3; sem = 5
    
    branch = name.split("_")[0]
    if program == "BS-MS" and "DS_AI" in name: branch = "DS+AI"
    if program == "BS-MS" and "IT" in name: branch = "IT"
    if branch == "MNC": branch = "MnC"
    
    return program, year, sem, branch, lab_group

def norm_time(t):
    t = (t or "").strip().lower()
    is_pm = "pm" in t
    is_am = "am" in t
    t = t.replace("am", "").replace("pm", "").strip()
    p = t.split(":")
    if len(p) == 2:
        try:
            hr = int(p[0])
            if is_pm and hr != 12: hr += 12
            elif is_am and hr == 12: hr = 0
            elif not is_pm and not is_am:
                if 1 <= hr <= 7: hr += 12
            return "{:02d}:{:02d}".format(hr, int(p[1]))
        except ValueError:
            pass
    return t

def guess_ctype(cc):
    return "Core" # Labs are usually core, electives have their own handling

def extract_tables_from_md(filepath, base_lab_group):
    rows = []
    lines = filepath.read_text(encoding="utf-8").splitlines()
    current_group = None
    
    in_table = False
    for line in lines:
        if line.startswith("## "):
            # Detect section
            header = line.lower()
            if "whole cohort" in header or "no subgroup" in header:
                current_group = None
            else:
                current_group = base_lab_group
        
        if line.startswith("|") and "Day" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 5:
                day, time_str, course, faculty, room = parts[0:5]
                dow = DAY_MAP.get(day)
                if dow is None: continue
                
                t_parts = time_str.split("-")
                if len(t_parts) == 2:
                    st = norm_time(t_parts[0])
                    et = norm_time(t_parts[1])
                else:
                    st = et = None
                
                cc = course.split()[0] if " " in course else course
                cc = cc.upper()
                cn = course # just use raw for now
                
                rows.append({
                    "day_of_week": dow,
                    "start_time": st,
                    "end_time": et,
                    "course_code": cc,
                    "course_name": cn,
                    "faculty_name": faculty,
                    "room": room,
                    "lab_group": current_group
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--semester",
        required=False,
        default=None,
        help=(
            "Semester label to stamp on every lab row, e.g. 'Autumn 2026-27'. "
            "Must exactly match CURRENT_SEMESTER_LABEL in the backend's .env, "
            "or service.py's semester filter will silently exclude every lab "
            "session this script inserts (NULL != 'Autumn 2026-27' in SQL)."
        ),
    )
    args = ap.parse_args()

    if not args.dry_run and not args.semester:
        print(
            "ERROR: --semester is required (except with --dry-run). Labs "
            "inserted without it get semester_label=NULL and will not appear "
            "for any student once CURRENT_SEMESTER_LABEL is set. "
            "Example: --semester 'Autumn 2026-27'"
        )
        sys.exit(1)

    
    env_file = SERVER_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    
    all_rows = []
    for f in DATA_DIR.glob("*.md"):
        if f.name == "Electives_All.md": continue
        
        program, year, sem, branch, base_lab_group = parse_filename(f.name)
        extracted = extract_tables_from_md(f, base_lab_group)
        
        for r in extracted:
            r["program"] = program
            r["year"] = year
            r["sem"] = sem
            r["branch"] = branch
            r["sec"] = None # Labs apply to all sections
            all_rows.append(r)
            
    print(f"Extracted {len(all_rows)} lab sessions.")
    
    if args.dry_run:
        for r in all_rows[:5]: print(r)
        return
        
    import db.connection as dbc
    
    # We DO NOT clear timetable_master here, we just insert labs
    # However, to avoid duplicate inserts on re-runs, we delete existing labs
    # -- scoped to this semester only, so re-running for a new semester
    # doesn't wipe out a previous semester's still-relevant lab rows.
    print(f"Clearing old lab sessions for semester '{args.semester}'...")
    dbc.execute(
        "DELETE FROM timetable_master WHERE (lab_group IS NOT NULL OR session_type IN ('lab', 'tutorial')) "
        "AND semester_label = %s",
        (args.semester,),
    )

    SQL = (
        "INSERT INTO timetable_master "
        "(year,sem,sec,day_of_week,start_time,end_time,"
        "course_code,course_name,session_type,room,faculty_name,course_type,program,branch,lab_group,semester_label) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )
    
    insert_data = []
    for r in all_rows:
        session_type = "tutorial" if "tutorial" in r["course_name"].lower() else "lab"
        insert_data.append((
            r["year"], r["sem"], r["sec"], r["day_of_week"], r["start_time"], r["end_time"],
            r["course_code"], r["course_name"], session_type, r["room"], r["faculty_name"],
            "Core", r["program"], r["branch"], r["lab_group"], args.semester
        ))
        
    dbc.executemany(SQL, insert_data)
    print("Done inserting lab sessions.")

if __name__ == "__main__":
    main()