"""
B6 — ERP Context Builder.

Converts raw ERP data (dicts from ERPConnector) into a readable
<personal_data> XML block that the LLM can parse unambiguously.
The wrapper tag tells the LLM this is live, authoritative personal data
— not a scraped public document — and the answer_generator system prompt
(see file 07 of the RBAC guide) tells it to say "Your CGPA is 8.34"
instead of "According to the retrieved document...".

Personal data is NEVER included in the public RAG `sources` list — the
`build()` method returns a string, not a sources dict, exactly because
there is no URL to cite for live ERP data.
"""



class ERPContextBuilder:

    def build(self, erp_results: dict, identity, access_result) -> str:
        """
        erp_results: dict of field → value, as returned by ERPConnector methods.
        identity:    Identity object (for display name / role context).
        access_result: AccessResult — scope_type is included so the LLM
                       knows whether it's seeing all grades or just one course.
        Returns: a plain-text string ready to be injected into the LLM context.
        """
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

        if "timetable" in erp_results and erp_results["timetable"]:
            tt = erp_results["timetable"]
            cohort = tt.get("cohort", {})
            slots = tt.get("timetable", [])
            if slots:
                lines.append(f"Student Weekly Class Timetable (Year {cohort.get('year')}, Sem {cohort.get('sem')}, Sec {cohort.get('sec')}):")
                lines.append("| Day | Time | Course Code | Course Name | Session Type | Room | Faculty |")
                lines.append("|---|---|---|---|---|---|---|")
                for s in slots:
                    lines.append(
                        f"| {s.get('day','')} | {s.get('start_time','')} - {s.get('end_time','')} | "
                        f"{s.get('course_code','')} | {s.get('course_name','')} | {s.get('session_type','')} | "
                        f"{s.get('room','N/A')} | {s.get('faculty_name','N/A')} |"
                    )
                lines.append("")

        lines.append("</personal_data>")
        return "\n".join(lines)


def _is_number(val) -> bool:
    try:
        float(str(val).replace("%", ""))
        return True
    except (ValueError, TypeError):
        return False
