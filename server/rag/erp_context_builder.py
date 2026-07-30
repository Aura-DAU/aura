# B6 — ERP Context Builder.
# Converts raw ERP data (dicts from ERPConnector) into a readable
# there is no URL to cite for live ERP data.



class ERPContextBuilder:

    def build(self, erp_results: dict, identity, access_result) -> str:
        # erp_results: dict of field → value, as returned by ERPConnector methods.
        # identity:    Identity object (for display name / role context).
        # Returns: a plain-text string ready to be injected into the LLM context.
        if not erp_results:
            return ""

        lines = [
            "<personal_data>",
            "Source: DAU ERP System (live, real-time data as of this request)",
            f"Access scope: {getattr(access_result, 'scope_type', 'self')}",
            "",
        ]

        if "profile" in erp_results and erp_results["profile"]:
            p = erp_results["profile"]
            lines += [
                "Student Profile:",
                f"  Name: {p.get('full_name', 'N/A')}",
                f"  Roll Number: {p.get('roll_number', 'N/A')}",
                f"  Program: {p.get('program', 'N/A')}, Dept: {p.get('dept', 'N/A')}",
                f"  Batch: {p.get('batch_year', 'N/A')}, Current Semester: {p.get('current_semester', 'N/A')}",
                "",
            ]

        if "cgpa" in erp_results and erp_results["cgpa"]:
            c = erp_results["cgpa"]
            cgpa_val = c.get("cgpa") or c.get("cgpa_raw_label", "N/A")
            sem_val  = c.get("as_of_semester", "latest")
            lines += [
                f"Current CGPA: {cgpa_val} (as of Semester {sem_val})",
                "",
            ]

        if "grades" in erp_results and erp_results["grades"]:
            lines.append("Course Grades:")
            for g in erp_results["grades"]:
                lines.append(
                    f"  {g.get('course_code','')} {g.get('course_name','')} "
                    f"(Sem {g.get('semester','')}): Grade {g.get('grade','N/A')} "
                    f"({g.get('grade_points','N/A')} points)"
                )
            lines.append("")

        if "attendance" in erp_results and erp_results["attendance"]:
            lines.append("Attendance:")
            for a in erp_results["attendance"]:
                pct = a.get("attendance_pct") or a.get("percentage", "N/A")
                attended  = a.get("attended_classes", "N/A")
                total     = a.get("total_classes", "N/A")
                pct_str   = f"{float(pct):.1f}%" if _is_number(pct) else str(pct)
                lines.append(
                    f"  {a.get('course_code','')} (Sem {a.get('semester','')}): "
                    f"{attended}/{total} classes = {pct_str}"
                )
            lines.append("")

        if "advisees" in erp_results and erp_results["advisees"]:
            lines.append("Advisees under your guidance:")
            for ad in erp_results["advisees"]:
                lines.append(
                    f"  {ad.get('student_roll_number','')} — {ad.get('full_name','')} "
                    f"({ad.get('dept','')} Sem {ad.get('current_semester','')})"
                )
            lines.append("")

        if "courses" in erp_results and erp_results["courses"]:
            lines.append("Your courses this semester:")
            for c in erp_results["courses"]:
                lines.append(
                    f"  {c.get('course_code','')} — Batch {c.get('batch','')} "
                    f"(Sem {c.get('semester','')})"
                )
            lines.append("")

        if "timetable" in erp_results and erp_results["timetable"]:
            tt = erp_results["timetable"]
            slots = tt.get("timetable", []) if isinstance(tt, dict) else []
            cohort = tt.get("cohort", {}) if isinstance(tt, dict) else {}
            is_common = tt.get("is_common", False) if isinstance(tt, dict) else False
            if slots:
                label = (
                    f"Year {cohort.get('year','?')}, Sem {cohort.get('sem','?')}, "
                    f"Section {cohort.get('sec','?')}"
                )
                if is_common:
                    lines.append(f"Weekly Timetable (common schedule — section not yet configured, {label}):")
                else:
                    lines.append(f"Weekly Timetable ({label}):")
                # Group by day
                by_day: dict = {}
                for s in slots:
                    day = s.get("day", "Unknown")
                    by_day.setdefault(day, []).append(s)
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for day in day_order:
                    if day not in by_day:
                        continue
                    lines.append(f"  {day}:")
                    for s in by_day[day]:
                        start = str(s.get("start_time", ""))[:5]
                        end   = str(s.get("end_time",   ""))[:5]
                        code  = s.get("course_code", "")
                        name  = s.get("course_name", "")
                        room  = s.get("room", "")
                        fac   = s.get("faculty_name", "")
                        stype = s.get("session_type", "")
                        detail = f"{start}–{end}  {code} {name}"
                        if stype:
                            detail += f" [{stype}]"
                        if room:
                            detail += f"  Room: {room}"
                        if fac:
                            detail += f"  Faculty: {fac}"
                        lines.append(f"    {detail}")
                lines.append("")

        lines.append("</personal_data>")
        return "\n".join(lines)


def _is_number(val) -> bool:
    try:
        float(str(val).replace("%", ""))
        return True
    except (ValueError, TypeError):
        return False
