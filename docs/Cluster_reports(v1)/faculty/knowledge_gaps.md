# Knowledge Gaps: Faculty Cluster

**Team C – Faculty Cluster**  
**Date:** 2026-06-10  

---

# Knowledge Gaps: Faculty Cluster

**Purpose:** Document failed queries identified during the RAG evaluation of the Faculty cluster question bank, analyze the root cause of each failure, and specify the required missing information.

---

## 🔍 Semantic Category Gaps & Specific Failed Questions

The evaluation identified 26 queries that failed because of missing context or incorrect retrieval alignment. These are categorized below:

### Gap 1: Faculty Directory Navigation & Website Features
* **Failure Description:** The RAG system lacks meta-information regarding how the website's directory is operated, structured, filtered, or searched.
* **Failed Questions:**
  * `FAC002`: *Where can I find the official faculty list?*
  * `FAC003`: *How do I access faculty profiles?*
  * `FAC004`: *What information is available in faculty profiles?*
  * `FAC005`: *Where is the DA-IICT faculty directory hosted?*
  * `FAC006`: *How can I search for a specific faculty member?*
  * `FAC008`: *Where can I find faculty email addresses?*
  * `FAC009`: *Does DA-IICT provide department-wise faculty listing?*
  * `FAC010`: *How is faculty information structured on the website?*
  * `FAC011`: *Can I view faculty designations online?*
  * `FAC012`: *Where can I find faculty office locations?*
  * `FAC013`: *Is the faculty directory updated regularly?*
  * `FAC014`: *Can I filter faculty by department?*
  * `FAC016`: *How detailed are faculty profiles at DA-IICT?*
  * `FAC018`: *Can students contact faculty directly?*
  * `FAC019`: *Is faculty profile information publicly accessible?*
  * `FAC020`: *Where is the main faculty database maintained?*
* **Missing Knowledge:** Explicit guide describing the search filters, department lists, data schema, office list mappings, and accessibility rules of the online directory.
* **Required Source:** DA-IICT Webmaster or IT administration guide.
* **Priority:** Medium

### Gap 2: Dean of Faculty Affairs Appointment & Office Details
* **Failure Description:** General biography pages are available, but details about the office room numbers or appointment procedures are missing from the scraped dataset.
* **Failed Questions:**
  * `FAC027`: *How is the Dean Faculty appointed?*
  * `FAC029`: *Where is the Dean Faculty office located?*
* **Missing Knowledge:** Selection and appointment procedures for the Dean of Faculty Affairs, and their physical office location on campus.
* **Required Source:** Faculty Handbook or Administration Office policies.
* **Priority:** Medium

### Gap 3: Adjunct & International Faculty Appointment Guidelines & Roles
* **Failure Description:** The RAG system retrieved historical annual reports or old NAAC files containing noise, but failed to locate any active guidelines defining the definition, status, and selection of adjunct professors.
* **Failed Questions:**
  * `FAC031`: *What are adjunct faculty members?*
  * `FAC034`: *What is the role of adjunct faculty?*
  * `FAC035`: *Are adjunct faculty full-time employees?*
  * `FAC036`: *How are adjunct faculty selected?*
  * `FAC038`: *Where is international adjunct faculty information available?*
* **Missing Knowledge:** Clear, structured policy document on the appointment, criteria, expectations, and status of adjunct and international visiting faculty.
* **Required Source:** Registrar Office or Academic Dean policies.
* **Priority:** High

### Gap 4: Centralized Research Output and Searching
* **Failure Description:** The system can search individual profile documents, but has no context on whether a centralized library database exists for searching across all publications.
* **Failed Questions:**
  * `FAC044`: *Is there a database for faculty research output?*
  * `FAC045`: *Can I search faculty publications by name?*
  * `FAC048`: *Where is publication data stored?*
* **Missing Knowledge:** Reference documentation about the DA-IICT Library repository (e.g., IRINS or library search system) for tracking research papers.
* **Required Source:** DA-IICT Library guide or IRINS portal documentation.
* **Priority:** Medium

---

## 🛠️ Technical / Rate Limit Failures
* **Failed Questions:** `FAC058` to `FAC150` (mostly rate-limited).
* **Failure Reason:** The Groq API hit the Tokens Per Day (TPD) limit of `100,000` tokens for the `llama-3.3-70b-versatile` model during bulk sequential processing of large prompt contexts.
* **Missing Knowledge:** N/A (Technical limit of API keys).
* **Required Source:** Upgrade Groq key tier, implement local embedding models, or increase retry-backoff times with rate limit handling in the evaluator.
* **Priority:** High (Technical blocker)
