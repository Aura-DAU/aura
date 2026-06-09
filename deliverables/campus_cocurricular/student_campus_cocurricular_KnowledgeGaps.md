# Knowledge Gaps Report — Campus Life & Co-Curricular Cluster (Level 1)

**Team:** Campus Life & Co-Curricular  
**Cluster Type:** Campus & Co-Curricular  
**Layer Focus:** Level 1 (Static / Already Collected Information)  
**Evaluation Date:** 2026-06-09  
**Total Questions Evaluated:** 250  
**RAG Configuration Tested:** `top_k = 1`  
**Question Bank Source:** `student_campus_life_QuestionBank.csv`  

---

## 📊 Summary Statistics

| Metric | Count | Percentage |
|---|---|---|
| **Total Questions** | 250 | 100% |
| **PASS** | 233 | 93.2% |
| **PARTIAL FAIL** | 13 | 5.2% |
| **FAIL** | 4 | 1.6% |
| **Overall Pass Rate** | **233/250** | **93.2%** |

> [!NOTE]
> All evaluations were performed using `top_k=1` (single retrieved document per query). The high PASS rate for Level 1 reflects the excellent completeness of static data collected. Issues are primarily due to retrieval limitations when the answer requires a less prominent secondary file.

---

## 🔴 Critical Knowledge Gaps (FAIL — System Cannot Answer)

These questions result in incorrect or "I don't have information" responses because the required document is not retrieved at `top_k=1` and the primary file (`dean_students.md`) does not contain the needed details.

### Gap 1: DCEI (DAU Centre for Entrepreneurship and Innovation) Details
**Affected Questions:** Q110, Q111, Q112, Q113  
**Source File Required:** `data/student_services/committees/entrepreneurship_cell.md`  
**Failure Reason:** At `top_k=1`, queries about DCEI likely retrieve `dean_students.md` (the dominant campus life document), which does not contain DCEI-specific information such as its founding year, mission statement, number of incubatees, and institutional backers.

**Impact:** 4 questions fully unanswerable.

**Recommended Fix:**
- Ensure `entrepreneurship_cell.md` content is chunked and embedded with strong metadata keywords (DCEI, Entrepreneurship Cell, Incubation, Startup).
- Add a brief DCEI summary to `dean_students.md` with a cross-reference to the full file.
- Consider increasing `top_k` to 3+ for production queries.

---

## 🟡 Partial Failures (Incomplete or Potentially Incorrect Answers)

These questions are answered but with missing depth, incomplete data, or answered from a less precise source document. With `top_k=1`, the top retrieved chunk may not contain the most accurate or complete answer.

### Gap 2: Medical Insurance Coverage Amount Discrepancy
**Affected Question:** Q195  
**Source Files:** `data/infrastructure/medical_facility.md` vs `data/student_services/medical_assistance_sop.md`  
**Issue:** **Critical data inconsistency.** `medical_facility.md` states coverage of **₹2.50 lakh per annum**, while the more recent `medical_assistance_sop.md` (2025-26 SOP) states **₹40,000 per student**. Depending on which document is retrieved at top_k=1, the system will give two different answers.

**Impact:** Students could receive incorrect insurance coverage information — this is a high-severity gap with real-world consequences.

**Recommended Fix:**
- **Immediately reconcile** the coverage amount between the two source documents.
- Update the older `medical_facility.md` to reflect the current SOP value (₹40,000) with the correct academic year reference.
- Flag this for urgent review by the admin/student services team.

### Gap 3: Doctor Visiting Hours Discrepancy (Dr. Arvindsinh Vaghela)
**Affected Question:** Q187  
**Source Files:** `data/infrastructure/medical_facility.md` vs `data/student_services/medical_assistance_sop.md`  
**Issue:** `medical_facility.md` states Dr. Vaghela's hours as **08:00–09:00 hrs**, while `medical_assistance_sop.md` states **09:00 AM – 10:00 AM (Mon-Sat)**. These differ by 1 hour and the RAG system (at `top_k=1`) will return only one version.

**Recommended Fix:**
- Cross-verify actual hours with the Medical Centre and update both files to be consistent.
- Ensure `medical_assistance_sop.md` (more recently dated, official SOP) is treated as the authoritative source.

### Gap 4: Grievance Redressal Cell (GRHS) Details
**Affected Questions:** Q213, Q214, Q215, Q243  
**Source File Required:** `data/student_services/committees/grievance_redressal_cell.md`  
**Failure Reason:** At `top_k=1`, generic campus queries may retrieve `dean_students.md` rather than `grievance_redressal_cell.md`. The dean's file only briefly mentions the grievance cell without providing:
- Types of grievances that can be raised
- Out-of-scope matters for the GRHS
- Step-by-step dispute resolution process

**Impact:** 4 questions partially or fully unanswerable in detail.

**Recommended Fix:**
- Add targeted metadata tags to `grievance_redressal_cell.md` for better retrieval (e.g., "grievance", "GRHS", "complaint", "dispute").
- Add a summary of grievance categories to `dean_students.md` with a reference to the dedicated file.

### Gap 5: First-Year Student Guidance Details
**Affected Questions:** Q225, Q226  
**Source File Required:** `data/student_services/first_year_in_campus.md`  
**Failure Reason:** At `top_k=1`, general student queries may retrieve `dean_students.md` or `dean_students_tab.md` instead of the dedicated `first_year_in_campus.md`, missing specific advice about campus life expectations and academic guidance for new students.

**Impact:** 2 questions partially answered without the specific first-year context.

**Recommended Fix:**
- Improve chunking of `first_year_in_campus.md` to include query-friendly keywords ("first year", "new student", "what to expect", "freshers").
- Consider adding a "First Year Guidance" section summary to `dean_students.md`.

---

## 🟢 Well-Covered Areas (No Gaps)

The following topic areas in Level 1 are **fully covered** with no retrieval failures at `top_k=1`:

| Topic Area | Questions | Pass Rate | Notes |
|---|---|---|---|
| **Dean of Students / Officials** | Q001–Q005 | 100% | dean_students.md is authoritative and comprehensive |
| **SBG Core Team & Structure** | Q006–Q014 | 100% | All SBG data in a single well-indexed file |
| **Research Body Government** | Q015–Q017 | 100% | RBG data present in dean_students.md |
| **All 8 Student Committees** | Q018–Q042 | 100% | All committee details in dean_students.md |
| **All 22 Student Clubs** | Q043–Q109 | 100% | All club data complete in dean_students.md |
| **Sports Facilities** | Q114–Q126 | 100% | sports_complex.md well-indexed and comprehensive |
| **Hostel Facilities** | Q127–Q150 | 100% | halls_of_residence.md + dean_students.md cover all points |
| **Hostel Rules & Policies** | Q151–Q178 | 100% | hostel_rules_and_regulations.md fully structured and retrievable |
| **Food Courts** | Q179–Q185 | 100% | food_court.md covers all cafeteria questions |
| **Medical Facilities (basic)** | Q186–Q207 | 97% | Minor discrepancy in two questions (Q187, Q195) |
| **Cultural Activities & Events** | Q217–Q220 | 100% | Annual Festival Committee section in dean_students.md |
| **Campus Security** | Q221–Q223 | 100% | campus_security.md concise and accurate |
| **Campus Location & Identity** | Q227–Q228 | 100% | location_contact.md reliable |

---

## 📋 Prioritized Action Items

### Priority 1 — Data Quality (Fix Immediately)
1. **Reconcile medical insurance coverage amount** between `medical_facility.md` (₹2.50 lakh) and `medical_assistance_sop.md` (₹40,000). Determine the correct current value and update both files.
2. **Reconcile Dr. Vaghela's visiting hours** — verify actual hours and update both source files to match.

### Priority 2 — Retrieval Coverage (Improve Before Production)
3. **DCEI content integration**: Add a section in `dean_students.md` linking to DCEI or embed its key data points. Ensure `entrepreneurship_cell.md` has metadata optimized for its specific queries.
4. **Grievance Redressal Cell retrieval**: Optimize metadata and add cross-reference summary in `dean_students.md`.

### Priority 3 — Minor Improvements (Good to Have)
5. **First-year guidance retrieval**: Ensure `first_year_in_campus.md` is indexed with first-year-specific query keywords.
6. **Increase top_k in production**: For complex or multi-source questions, consider `top_k=3` to reduce retrieval misses across siloed files.

---

## 🔍 Retrieval Limitation Analysis (top_k=1)

With `top_k=1`, the RAG system is significantly constrained:

- **Dominant file problem**: `dean_students.md` (17,854 bytes, comprehensive) tends to be the top match for most Campus Life queries, which is usually correct but causes it to "shadow" smaller specialized files like `entrepreneurship_cell.md` or `grievance_redressal_cell.md`.
- **Cross-file answers**: Questions that require synthesis from two files (e.g., Q195 about insurance from both `medical_facility.md` and `medical_assistance_sop.md`) are especially vulnerable at `top_k=1`.
- **Recommendation**: For Level 1 evaluation, `top_k=3` is the minimum recommended setting to reliably cover the full breadth of the Campus Life & Co-Curricular cluster.

---

## 📁 Source Files Analyzed (Level 1)

| File | Size | Coverage |
|---|---|---|
| `data/student_services/dean_students.md` | 17,854 bytes | SBG, Committees, Clubs, Wardens, DAC |
| `data/infrastructure/halls_of_residence.md` | 2,500 bytes | Hostel facilities, capacity |
| `data/infrastructure/sports_complex.md` | 2,004 bytes | Sports facilities, coaching phases |
| `data/infrastructure/medical_facility.md` | 2,336 bytes | Doctors, hospitals, insurance |
| `data/infrastructure/food_court.md` | 1,104 bytes | Food courts, cuisine types |
| `data/infrastructure/campus_security.md` | 1,212 bytes | Security setup |
| `data/student_services/medical_assistance_sop.md` | 9,532 bytes | Emergency SOP, nurses, hospitals |
| `data/student_services/rules/hostel_rules_and_regulations.md` | 9,876 bytes | All hostel rules and fines |
| `data/student_services/contact/location_contact.md` | 5,742 bytes | Campus location, contact |
| `data/student_services/committees/entrepreneurship_cell.md` | 3,328 bytes | DCEI — ⚠️ retrieval gap |
| `data/student_services/committees/grievance_redressal_cell.md` | 2,214 bytes | GRHS — ⚠️ retrieval gap |
| `data/student_services/first_year_in_campus.md` | 7,386 bytes | First-year guidance — ⚠️ minor gap |

---

*Report generated by: Campus Life & Co-Curricular Cluster Team*  
*Branch: `Dhruvam/campus-cocurricular-cluster`*  
*Deliverable File: `student_campus_cocurricular_KnowledgeGaps.md`*
