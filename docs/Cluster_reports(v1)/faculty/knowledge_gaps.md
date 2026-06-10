# Knowledge Gaps: Faculty Cluster

**Team C – Faculty Cluster**  
**Date:** 2026-06-10  

---

# Knowledge Gaps: Faculty Cluster

**Purpose:** Document failed queries identified during the RAG evaluation of the Faculty cluster question bank, analyze the root cause of each failure, and specify the required missing information.

---

## 🔍 Semantic Category Gaps & Specific Failed Questions

The evaluation identified 47 queries that failed because of missing context or incorrect retrieval alignment. These are categorized below:

### Gap 1: Faculty Directory Navigation & Website/System Infrastructure
* **Failure Description:** The RAG system lacks meta-information regarding how the website's directory is operated, structured, filtered, or searched, and is missing database-level schemas or API/centralization details of the directory itself.
* **Failed Questions:**
  * `FAC002`: *Where can I find the official faculty list?*
  * `FAC003`: *How do I access faculty profiles?*
  * `FAC005`: *Where is the DA-IICT faculty directory hosted?*
  * `FAC006`: *How can I search for a specific faculty member?*
  * `FAC008`: *Where can I find faculty email addresses?*
  * `FAC009`: *Does DA-IICT provide department-wise faculty listing?*
  * `FAC010`: *How is faculty information structured on the website?*
  * `FAC011`: *Can I view faculty designations online?*
  * `FAC012`: *Where can I find faculty office locations?*
  * `FAC013`: *Is the faculty directory updated regularly?*
  * `FAC014`: *Can I filter faculty by department?*
  * `FAC018`: *Can students contact faculty directly?*
  * `FAC019`: *Is faculty profile information publicly accessible?*
  * `FAC020`: *Where is the main faculty database maintained?*
  * `FAC141`: *What is the overall faculty structure at DA-IICT?*
  * `FAC142`: *How many departments have faculty listings?*
  * `FAC143`: *Are emeritus faculty listed separately?*
  * `FAC145`: *Is research interest searchable in faculty directory?*
  * `FAC148`: *Is faculty data accessible via API?*
  * `FAC149`: *Is the faculty database centralized?*
* **Missing Knowledge:** Explicit guide describing the search filters, department lists, data schema, office list mappings, and accessibility rules of the online directory.
* **Required Source:** DA-IICT Webmaster or IT administration guide.
* **Priority:** Medium

### Gap 2: Adjunct & International Faculty Guidelines
* **Failure Description:** The RAG system retrieved historical reports containing lists of names, but failed to retrieve any formal document detailing rules, policies, selection criteria, or structural roles for adjunct and international faculty.
* **Failed Questions:**
  * `FAC031`: *What are adjunct faculty members?*
  * `FAC033`: *Does DA-IICT have international adjunct faculty?*
  * `FAC034`: *What is the role of adjunct faculty?*
  * `FAC035`: *Are adjunct faculty full-time employees?*
  * `FAC036`: *How are adjunct faculty selected?*
  * `FAC038`: *Where is international adjunct faculty information available?*
* **Missing Knowledge:** Clear, structured policy document on the appointment, criteria, expectations, and status of adjunct and international visiting faculty.
* **Required Source:** Registrar Office or Academic Dean policies.
* **Priority:** High

### Gap 3: Faculty Recruitment, Salary, & Tenure Policies
* **Failure Description:** Specific operational details regarding recruitment selection steps, tenure-track transition rules, detailed salary scales/bands, retirement age rules, and hiring criteria weights (like industry experience) are missing or not indexed.
* **Failed Questions:**
  * `FAC096`: *Are PhD holders required for faculty jobs?*
  * `FAC097`: *What is the selection process for faculty hiring?*
  * `FAC101`: *What is the tenure policy for faculty?*
  * `FAC104`: *What is the salary structure for faculty?*
  * `FAC108`: *What is the retirement policy for faculty?*
  * `FAC120`: *Is industry experience valued in hiring?*
* **Missing Knowledge:** Official DA-IICT Service Rules, Recruitment Guidelines, and Salary/Compensation policy docs.
* **Required Source:** Registrar Office or Human Resources.
* **Priority:** High

### Gap 4: Faculty Workload, Teaching, & Training Responsibilities
* **Failure Description:** The system cannot retrieve operational guidance on teaching workloads, specific duties for junior vs senior ranks, policies on teaching assistant assignment, guidelines for multidisciplinary course design, or mandatory professional training requirements.
* **Failed Questions:**
  * `FAC117`: *What is the academic workload of faculty?*
  * `FAC121`: *What teaching responsibilities do faculty have?*
  * `FAC135`: *What is expected from junior faculty?*
  * `FAC137`: *Are teaching assistants involved?*
  * `FAC139`: *Is interdisciplinary teaching encouraged?*
  * `FAC140`: *Are faculty required to attend training programs?*
* **Missing Knowledge:** Workload guidelines, Faculty Handbook sections on academic duties, TA allocation policies, and faculty development program requirements.
* **Required Source:** Office of Academic Affairs / Dean (Academic Programs).
* **Priority:** Medium

### Gap 5: Institutional Governance, Committees, & Course Proposals
* **Failure Description:** The RAG documents don't have concrete guidelines about the administrative roles of faculty, how course approval works, which standing committees faculty serve on, or placement coordination roles.
* **Failed Questions:**
  * `FAC124`: *Can faculty propose new courses?*
  * `FAC125`: *Do faculty participate in committees?*
  * `FAC128`: *Are faculty involved in placements?*
  * `FAC129`: *What administrative roles do faculty hold?*
* **Missing Knowledge:** Governance and administrative policy manuals, academic senate guidelines for proposing courses, and placement cell structure.
* **Required Source:** Registrar Office or Senate minutes.
* **Priority:** Medium

### Gap 6: Centralized Research Repositories
* **Failure Description:** The system can search individual profile documents, but has no context on whether a centralized library database exists for searching across all publications.
* **Failed Questions:**
  * `FAC044`: *Is there a database for faculty research output?*
  * `FAC048`: *Where is publication data stored?*
* **Missing Knowledge:** Reference documentation about the DA-IICT Library repository (e.g., IRINS or library search system) for tracking research papers.
* **Required Source:** DA-IICT Library guide or IRINS portal documentation.
* **Priority:** Medium

### Gap 7: Faculty Dean Office & Handbook Meta-information
* **Failure Description:** Specific office locations, handbook maintenance cycles, and the exact role/integration of student feedback in annual appraisals are missing from the retrieved context.
* **Failed Questions:**
  * `FAC029`: *Where is the Dean Faculty office located?*
  * `FAC079`: *How often is the faculty handbook updated?*
  * `FAC113`: *Is student feedback used in evaluation?*
* **Missing Knowledge:** Physical location directory, handbook revision schedule, and faculty annual self-appraisal form instructions.
* **Required Source:** Office of the Director / Dean of Faculty Affairs.
* **Priority:** Low

---

## 🛠️ Technical / Rate Limit Failures
* **Failed Questions:** None.
* **Status:** All queries were successfully evaluated with 100% execution completion. There were 0 rate limit or technical failures.
