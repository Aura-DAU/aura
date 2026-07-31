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

        if ("profile" not in erp_results or not erp_results["profile"]) and identity is not None:
            erp_results["profile"] = {
                "full_name": getattr(identity, "full_name", None) or getattr(identity, "fullName", None) or "N/A",
                "roll_number": getattr(identity, "roll_number", None) or getattr(identity, "rollNumber", None) or getattr(identity, "erp_id", "N/A"),
                "program": getattr(identity, "program", None) or getattr(identity, "programme", "B.Tech. (ICT)"),
                "dept": getattr(identity, "dept", None) or getattr(identity, "department", None) or getattr(identity, "branch", "ICT"),
                "batch_year": getattr(identity, "batch_year", None) or getattr(identity, "batchYear", "2023"),
                "current_semester": getattr(identity, "current_sem", None) or getattr(identity, "currentSem", None) or getattr(identity, "current_semester", 5),
            }

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

        lines.append("</personal_data>")
        return "\n".join(lines)


def _is_number(val) -> bool:
    try:
        float(str(val).replace("%", ""))
        return True
    except (ValueError, TypeError):
        return False
