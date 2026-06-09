> **Team Campus Life & Co-Curricular**  
> **Done By:** Dhruvam  
> **Date:** 2026-06-09  

---

# Knowledge Gaps: Campus Life & Co-Curricular

**Purpose:** Identify missing knowledge based on failed evaluation questions and system audit.

## Level 1 Gaps (Static Knowledge Missing)

### Gap 1: DCEI (DAU Centre for Entrepreneurship and Innovation) Details
* **Question:** What is the mission of DCEI? How many incubates has it produced?
* **Failure Reason:** At `top_k=1`, queries about DCEI retrieve the generic `dean_students.md` instead of the specialized `entrepreneurship_cell.md` file. The general student info file does not contain specific incubation counts or institutional backers.
* **Missing Knowledge:** Key statistics on incubatees, detailed founding history, and official institutional/financial backers of the DCEI.
* **Required Source:** DCEI / Student Chapters & Societies coordinator.
* **Priority:** High

### Gap 2: Medical Insurance Coverage Discrepancy
* **Question:** What is the Group Mediclaim Insurance coverage amount for DAU students?
* **Failure Reason:** Conflicting information exists in the data directory. `medical_facility.md` states the coverage is **₹2.50 lakh per annum**, while `medical_assistance_sop.md` (the official SOP) states it is **₹40,000 per student**. The RAG system returns different figures depending on the chunk retrieved.
* **Missing Knowledge:** A reconciled, authoritative coverage figure matching the current academic year's policy.
* **Required Source:** Student Services / Accounts Office.
* **Priority:** High

### Gap 3: Doctor Visiting Hours Discrepancy
* **Question:** What are the visiting hours of Dr. Arvindsinh Vaghela at the Medical Centre?
* **Failure Reason:** Conflicting data exists. `medical_facility.md` lists the hours as **08:00 to 09:00 hrs**, while the newer `medical_assistance_sop.md` lists them as **09:00 AM – 10:00 AM**.
* **Missing Knowledge:** Verified current schedule for visiting campus doctors.
* **Required Source:** Medical Centre Admin / Student Services.
* **Priority:** Medium

### Gap 4: Grievance Redressal Cell (GRHS) Process
* **Question:** What types of grievances can students raise? What matters are out of scope?
* **Failure Reason:** At `top_k=1`, generic queries pull `dean_students.md` which only briefly mentions the cell. The specialized `grievance_redressal_cell.md` contains the full procedure but is shadowed by the larger file.
* **Missing Knowledge:** Detailed category list of grievances, exact step-by-step resolution process, and out-of-scope items.
* **Required Source:** Registrar's Office / Grievance Redressal Committee.
* **Priority:** Medium

### Gap 5: First-Year Student Guidance
* **Question:** What academic advice is given to first-year students at DAU?
* **Failure Reason:** Queries retrieve the primary student services file, missing the specific recommendations and expectations laid out in `first_year_in_campus.md`.
* **Missing Knowledge:** Orientation timetables, specific freshman transition checklists, and student advisory contact details.
* **Required Source:** Dean of Students Office.
* **Priority:** Low

---

## Level 2 Gaps (Dynamic Information Missing)

### Gap 6
* **Question:** What are the weekly schedules for student hobby club meetings?
* **Failure Reason:** While `dean_students.md` lists all 22 clubs and their convenors, it lacks dynamic weekly scheduling.
* **Missing Knowledge:** Real-time event timings, rooms booked for club workshops, and weekly practice sessions.
* **Required Source:** SBG / Individual Club Convenors — needs dynamic API or regular calendar sync.
* **Priority:** Medium

### Gap 7
* **Question:** What is the today's menu at the campus food courts?
* **Failure Reason:** `food_court.md` lists only static cuisine categories and contractors, not daily options.
* **Missing Knowledge:** Daily menu updates and pricing from the 7 campus food courts.
* **Required Source:** Food Court Contractors / Cafeteria Management Committee (CMC) — requires database updates.
* **Priority:** Low

---

## Level 3 Gaps (Human-Provided Knowledge Missing)

### Gap 8
* **Question:** How does a student book the sports gymnasium or cricket field for a private/departmental match?
* **Failure Reason:** `sports_complex.md` describes the facility but does not outline the permission process.
* **Missing Knowledge:** Requisition forms, approval hierarchy (Physical Instructor -> Dean of Students), and non-academic booking rules.
* **Required Source:** Physical Education Instructor / Dean of Students.
* **Priority:** Medium

### Gap 9
* **Question:** What is the process for registering a new student hobby-driven club under the SBG?
* **Failure Reason:** General guidelines list the active 22 clubs but omit instructions for proposing new ones.
* **Missing Knowledge:** Minimum student signatures required, proposal format, and budget allocation procedures.
* **Required Source:** SBG Convenor / Dean of Students.
* **Priority:** Medium