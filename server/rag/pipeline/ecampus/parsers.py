"""
HTML parsers for ecampus.daiict.ac.in tab pages.

All parsers validated against real HTML (July 2026) from:
  - StudentDetailEditServlet
  - StudentRegistrationListServlet
  - StudentRegistrationEditServlet  (registration form with courses)
  - GradeSemesterListServlet        (semester list)
  - GradeCourseListServlet          (grade card per semester)

Key structural facts confirmed from real HTML:
  - Java servlet portal, NOT ASP.NET
  - Tables use class="listtbl" for list views, class="formtbl" for forms
  - Student detail is a label/value form (NOT a grid table)
  - Registration list shows semesters, clicking "Edit" POSTs to
    StudentRegistrationEditServlet with stdid + SemesterID hidden fields
  - Grade card shows per-course grades AND a summary row with SPI/CPI
  - Attendance tab URL confirmed: AttandanceSemesterListServlet
    (note: typo in real portal — "Attandance" not "Attendance")
  - Logout confirmed: /webapp/intranet/LoginServlet?logout=true
"""

import re
from bs4 import BeautifulSoup


# ── Student Detail ─────────────────────────────────────────────────────────
def parse_student_detail(html: str) -> dict:
    """
    StudentDetailEditServlet — label/value form layout.
    Confirmed fields from real HTML:
      - Student Name  → hidden input STDFIRSTNAME
      - Student Id    → hidden input STDINSTID
      - Date of Birth → input STDDOB
      - Gender        → input STDGENDER
      - Programme     → visible in Registration form as "B Tech (ICT)"
      - Batch         → hidden input STDBCHID (batch ID, not year)
      - Mobile        → inside textarea (PermAddrs)
      - Email         → inside textarea (PermAddrs)
      - Address       → textarea PermAddrs
    """
    soup = BeautifulSoup(html, "html.parser")

    def val(name):
        el = soup.find("input", {"name": name})
        return el["value"].strip() if el and el.get("value") else None

    def txt(name):
        el = soup.find("input", {"name": name})
        return el.get("value", "").strip() if el else None

    # Name from hidden field (clean, no trailing spaces)
    full_name = txt("STDFIRSTNAME") or ""

    # Student ID
    student_id = txt("STDINSTID")

    # DOB and gender from readonly inputs
    dob_el = soup.find("input", {"name": "STDDOB"})
    dob = dob_el["value"].strip() if dob_el else None

    gender_el = soup.find("input", {"name": "STDGENDER"})
    gender = gender_el["value"].strip() if gender_el else None

    # Address textarea — extract mobile and email
    address_text = ""
    mobile = None
    email = None
    textarea = soup.find("textarea", {"name": "PermAddrs"})
    if textarea:
        address_text = textarea.get_text(strip=False)
        mob_match = re.search(r"Student Mobile No\s*:\s*(\d+)", address_text)
        email_match = re.search(r"Email Id\s*:\s*([\w.@]+)", address_text)
        if mob_match:
            mobile = mob_match.group(1).strip()
        if email_match:
            email = email_match.group(1).strip()

    return {
        "full_name":   full_name.strip(),
        "student_id":  student_id,
        "dob":         dob,
        "gender":      "Male" if gender == "M" else "Female" if gender == "F" else gender,
        "mobile":      mobile,
        "email":       email,
        "address_raw": address_text.strip(),
    }


# ── Registration List ──────────────────────────────────────────────────────
def parse_registration_list(html: str) -> list[dict]:
    """
    StudentRegistrationListServlet — table with columns:
      Sr. No. | Semester | Registration Date | Action

    Returns list of semesters with their stdid and SemesterID
    (needed to POST to StudentRegistrationEditServlet for course details).

    Semester IDs extracted from onclick="fncEditRegister(stdid, semesterID)"
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="listtbl")
    if not table:
        return []

    semesters = []
    for tr in table.find_all("tr")[1:]:  # skip header
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue

        sr_no    = cells[0].get_text(strip=True)
        sem_name = cells[1].get_text(strip=True)
        reg_date = cells[2].get_text(strip=True).replace("\xa0", "").strip()

        # Extract stdid and SemesterID from onclick
        btn = cells[3].find("input", {"type": "button"})
        std_id = None
        sem_id = None
        if btn and btn.get("onclick"):
            match = re.search(r"fncEditRegister\((\d+),(\d+)\)", btn["onclick"])
            if match:
                std_id = match.group(1)
                sem_id = match.group(2)

        if sem_name:
            semesters.append({
                "sr_no":        sr_no,
                "semester":     sem_name,
                "reg_date":     reg_date if reg_date else None,
                "std_id":       std_id,
                "semester_id":  sem_id,
                "registered":   bool(reg_date),
            })

    return semesters


# ── Registration Edit (Course List for a Semester) ─────────────────────────
def parse_registration_courses(html: str) -> dict:
    """
    StudentRegistrationEditServlet — registration form for a specific semester.
    Confirmed fields from real HTML (Semester IV example):

    Header info:
      - Name, Program, Semester, Student ID, Batch, Date

    Course sections:
      - Regular courses (class="formtbl", rows with SRCSTATUS = ACTIVE)
      - Other Courses (REGULARADD)
      - Grade Improvement (REGULARGRADEIMPROVE)
      - Backlog (BACKLOG)
      - Audit (AUDIT)

    For each course: Semester, Title, Code, Credits, Status
    Credits format: "4.00\n(3.00+\n0.00+\n2.00)" → parse total only
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── Header info ──
    name = program = semester = student_id = batch = reg_date = None
    header_table = soup.find("table", class_="formtbl")
    if header_table:
        rows = header_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            labels = [c.get_text(strip=True) for c in cells]
            for i, lbl in enumerate(labels):
                val = labels[i + 1] if i + 1 < len(labels) else ""
                if lbl == "Name":       name = val
                elif lbl == "Program":  program = val
                elif lbl == "Semester": semester = val.replace("\n", " ").strip()
                elif lbl == "Student ID": student_id = val
                elif lbl == "Batch":    batch = val
                elif lbl == "Date":     reg_date = val

    # ── Course rows ──
    courses = []
    # All formtbl tables after the header contain courses
    all_tables = soup.find_all("table", class_="formtbl")
    for tbl in all_tables[1:]:  # skip the header table
        rows = tbl.find_all("tr")
        for row in rows:
            cells = row.find_all("td", class_="formfld")
            if len(cells) < 3:
                continue

            # Regular course rows have: Semester | Title | Code | Credits | Status
            texts = [c.get_text(" ", strip=True) for c in cells]

            # Detect if this looks like a course row (has a course code pattern)
            course_code = None
            course_name = None
            credits_raw = None
            status = None
            course_type = None

            if len(texts) >= 4:
                # Check for hidden SRCTYPE to determine course type
                src_type = cells[-1].find("input", {"name": re.compile(r"SRCTYPE\d+")})
                if src_type:
                    course_type = src_type.get("value", "REGULAR")

                # Status cell — last td with formfld
                status_text = texts[-1].strip()
                if status_text in {"ACTIVE", "INACTIVE", "DROPPED"}:
                    status = status_text

                # Course structure: sem | title | code | credits | status
                if len(texts) >= 5:
                    course_name = texts[1].strip()
                    course_code = texts[2].strip()
                    credits_raw = texts[3].strip()
                elif len(texts) == 4:
                    # Other/backlog section: sr | description(title+code+credits) | register
                    combined = texts[1]
                    # Try to extract code (pattern like IT214, EL203, IE410)
                    code_match = re.search(r'\b([A-Z]{2,3}\d{3,4}[A-Z]?)\b', combined)
                    if code_match:
                        course_code = code_match.group(1).strip()
                        course_name = combined[:combined.find(course_code)].strip()
                    credits_raw = combined

            if course_code:
                # Parse total credits from "4.00\n(3.00+\n0.00+\n2.00)"
                total_credits = None
                credit_match = re.search(r'^([\d.]+)', credits_raw.replace("\n", " "))
                if credit_match:
                    total_credits = float(credit_match.group(1))

                courses.append({
                    "course_code":   course_code,
                    "course_name":   course_name,
                    "credits":       total_credits,
                    "status":        status or "ACTIVE",
                    "course_type":   course_type or "REGULAR",
                })

    return {
        "student_name": name,
        "program":      program,
        "semester":     semester,
        "student_id":   student_id,
        "batch":        batch,
        "reg_date":     reg_date,
        "courses":      courses,
    }


# ── Grade Semester List ────────────────────────────────────────────────────
def parse_grade_semester_list(html: str) -> list[dict]:
    """
    GradeSemesterListServlet — same table structure as registration list.
    Columns: Sr. No. | Semester | Registration Date | Action (Grade Card button)

    onclick="fncEditRegister(stdid, semesterID)" → POST to GradeCourseListServlet
    Only rows with a "Grade Card" button have results available.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="listtbl")
    if not table:
        return []

    semesters = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue

        sem_name = cells[1].get_text(strip=True)
        reg_date = cells[2].get_text(strip=True).replace("\xa0", "").strip()

        btn = cells[3].find("input", {"type": "button", "value": "Grade Card"})
        std_id = sem_id = None
        if btn and btn.get("onclick"):
            match = re.search(r"fncEditRegister\((\d+),(\d+)\)", btn["onclick"])
            if match:
                std_id = match.group(1)
                sem_id = match.group(2)

        if sem_name:
            semesters.append({
                "semester":        sem_name,
                "reg_date":        reg_date if reg_date else None,
                "has_grades":      btn is not None,
                "std_id":          std_id,
                "semester_id":     sem_id,
            })

    return semesters


# ── Grade Card (per semester) ──────────────────────────────────────────────
def parse_grade_card(html: str) -> dict:
    """
    GradeCourseListServlet — grade card for one semester.
    Confirmed structure from real HTML:

    Header table (class=formtbl, first):
      Name | Program | Semester
      Student ID | Batch | Date

    Course grades table (class=formtbl, second):
      COURSE TITLE | COURSE CODE | CREDIT HOURS | GRADE | GRADE POINTS | REMARKS

    Performance summary table (class=formtbl, last):
      Current semester: CREDITS REGISTERED | CREDITS EARNED | GRADE POINTS EARNED | SPI
      Cumulative:       CREDITS REGISTERED | CREDITS EARNED | GRADE POINTS EARNED | CPI

    Real example (Semester IV):
      IT214 Database Management System — BB — 32.0 points
      EL203 Embedded Hardware Design   — AA — 40.0 points
      SPI = 9.35, CPI = 8.54
    """
    soup = BeautifulSoup(html, "html.parser")
    all_tables = soup.find_all("table", class_="formtbl")

    name = program = semester = student_id = batch = None
    courses = []
    spi = cpi = None
    credits_registered_sem = credits_earned_sem = grade_points_sem = None
    credits_registered_cum = credits_earned_cum = grade_points_cum = None

    for idx, tbl in enumerate(all_tables):
        rows = tbl.find_all("tr")
        headers = [th.get_text(strip=True) for th in rows[0].find_all("td")] if rows else []

        # ── Header table (Name, Program, Semester, Student ID, Batch) ──
        if "Name" in headers or (headers and "COURSE TITLE" not in headers and "CREDITS REGISTERED" not in headers and idx == 0):
            for row in rows:
                cells = row.find_all("td")
                texts = [c.get_text(" ", strip=True) for c in cells]
                for i, t in enumerate(texts):
                    nxt = texts[i+1].strip() if i+1 < len(texts) else ""
                    if t == "Name":       name = nxt
                    elif t == "Program":  program = nxt
                    elif t == "Semester": semester = nxt.replace("\n", " ").strip()
                    elif t == "Student ID": student_id = nxt
                    elif t == "Batch":    batch = nxt

        # ── Course grades table ──
        elif "COURSE TITLE" in headers:
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                texts = [c.get_text(" ", strip=True) for c in cells]
                course_name  = texts[0].strip()
                course_code  = texts[1].strip()
                credits_raw  = texts[2].strip()
                grade        = texts[3].strip()
                grade_points = texts[4].strip()

                # Parse total credits
                total_credits = None
                cm = re.search(r'^([\d.]+)', credits_raw)
                if cm:
                    total_credits = float(cm.group(1))

                # Parse grade points (may be "--" for P/F courses)
                gp_val = None
                try:
                    gp_val = float(grade_points.replace("--", "").strip())
                except ValueError:
                    pass

                if course_code:
                    courses.append({
                        "course_name":   course_name,
                        "course_code":   course_code.strip(),
                        "credits":       total_credits,
                        "grade":         grade,
                        "grade_points":  gp_val,
                    })

        # ── Performance summary table ──
        elif "SPI" in headers or "CPI" in headers:
            data_rows = [r for r in rows if r.find("td", class_="formfld")]
            if data_rows:
                cells = data_rows[0].find_all("td")
                texts = [c.get_text(strip=True).replace("\xa0", "").strip() for c in cells]
                if len(texts) >= 8:
                    try: credits_registered_sem = float(texts[0])
                    except (ValueError, TypeError): pass
                    try: credits_earned_sem = float(texts[1])
                    except (ValueError, TypeError): pass
                    try: grade_points_sem = float(texts[2])
                    except (ValueError, TypeError): pass
                    try: spi = float(texts[3])
                    except (ValueError, TypeError): pass
                    try: credits_registered_cum = float(texts[4])
                    except (ValueError, TypeError): pass
                    try: credits_earned_cum = float(texts[5])
                    except (ValueError, TypeError): pass
                    try: grade_points_cum = float(texts[6])
                    except (ValueError, TypeError): pass
                    try: cpi = float(texts[7])
                    except (ValueError, TypeError): pass

    return {
        "student_name":            name,
        "program":                 program,
        "semester":                semester,
        "student_id":              student_id,
        "batch":                   batch,
        "courses":                 courses,
        "spi":                     spi,
        "cpi":                     cpi,
        "credits_registered_sem":  credits_registered_sem,
        "credits_earned_sem":      credits_earned_sem,
        "grade_points_sem":        grade_points_sem,
        "credits_registered_cum":  credits_registered_cum,
        "credits_earned_cum":      credits_earned_cum,
        "grade_points_cum":        grade_points_cum,
    }


# ── Also confirmed from menu JS in real HTML ───────────────────────────────
# Attendance URL: /webapp/intranet/AttandanceSemesterListServlet  (typo is real)
# Logout URL:     /webapp/intranet/LoginServlet?logout=true
# Hostel submenu: BulletinListDisplayServlet, StudentComplainListServlet,
#                 HostelStudentLeavesListServlet, HostelVisitRoomBookingsListServlet,
#                 HostelPolicyListDisplayServlet
# Fee receipts:   CandidateReceiptsViewServlet
#                 SemSelector?target=StudentReceiptsViewServlet&actiontext=List Semesters