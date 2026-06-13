# Coverage Map: Faculty Cluster

**Team C – Faculty Cluster**  
**Date:** 2026-06-10  

---

# Coverage Map: Faculty Cluster

**Purpose:** Measure what faculty-related information is available and missing for the Faculty cluster, focusing on Layer 1 (Static/Collected) of the [sc_faculty.png](file:///Users/vedant_shah/Desktop/Student_clusters/sc_faculty.png) diagram.

## Level 1 – Information Available (From Current Sources)

All 8 official Layer 1 topics identified in the Faculty Information Cluster Maturity & Coverage diagram are covered in the dataset.

* **1. Faculty Profiles & Directory** – **Available**
  * **Description:** Comprehensive directory list of regular, adjunct, international adjunct, distinguished, and visiting faculty.
  * **Source Files:**
    * `data/faculty/regular/faculty_list.md`
    * `data/faculty/adjunct/adjunct_faculty.md`
    * `data/faculty/teaching_fellows_list.md`
    * Profiles under `data/faculty/regular/` (76 files) and `data/faculty/adjunct/` (28 files)

* **2. Faculty Qualifications & Expertise** – **Available**
  * **Description:** Academic qualifications (B.Tech, M.Tech, PhD, Postdoc) and universities graduated from.
  * **Source Files:**
    * "Education" and "Biography" sections in individual profiles under `data/faculty/regular/*.md` (e.g., `faculty_abhishek_jindal.md`, `faculty_aditya_tatu.md`)

* **3. Faculty Designation & Department** – **Available**
  * **Description:** Academic rank/designation (Professor, Associate Professor, Assistant Professor, Lecturer, Dean) and department/specialization area.
  * **Source Files:**
    * `data/faculty/regular/faculty_list.md`
    * `data/faculty/dean_faculty.md`
    * "Biography" and "Overview" sections of individual profiles under `data/faculty/regular/*.md`

* **4. Faculty Publications** – **Available**
  * **Description:** Research papers, journal articles, conference papers, and patents authored by faculty.
  * **Source Files:**
    * "Publications" and "Journal Articles" sections in individual profiles under `data/faculty/regular/*.md` and `data/faculty/adjunct/*.md`

* **5. Research Interests** – **Available**
  * **Description:** Broad research fields and specific academic specialization topics.
  * **Source Files:**
    * "Specialization" section in individual profiles under `data/faculty/regular/*.md` and `data/faculty/adjunct/*.md`

* **6. Faculty Accomplishments** – **Available**
  * **Description:** Professional milestones, key administrative appointments, and career history.
  * **Source Files:**
    * "Biography" and "Overview" sections in individual profiles under `data/faculty/regular/*.md`

* **7. Faculty Contact Information** – **Available**
  * **Description:** Official email addresses, phone extensions, office locations, and Google Scholar/personal page URLs.
  * **Source Files:**
    * "Contact Information" and "Website Links" sections in individual profiles under `data/faculty/regular/*.md` and `data/faculty/adjunct/*.md`

* **8. Awards & Recognitions** – **Available**
  * **Description:** Prestigious fellowships, best paper awards, distinguished lectureship appointments, and institutional honors.
  * **Source Files:**
    * "Awards & Recognition" or "Accomplishments" sections in individual profiles under `data/faculty/regular/*.md` and news/achievements documents (e.g., `data/faculty/regular/faculty_rutu_parekh.md`, etc.)

---

## Coverage Summary: 100%

* **Total Level 1 Topics Identified in Diagram:** 8
* **Total Level 1 Topics Available in Codebase:** 8
* **Overall Coverage Score:** 100% (8/8)
