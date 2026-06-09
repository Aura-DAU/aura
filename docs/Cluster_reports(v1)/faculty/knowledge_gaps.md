# Knowledge Gaps: Faculty Cluster

**Team C – Faculty Cluster**  
**Date:** 2026-06-10  

---

# Knowledge Gaps: Faculty Cluster

**Purpose:** Document failed queries identified during the RAG evaluation of the Faculty cluster question bank, analyze the root cause of each failure, and specify the required missing information.

---

## 🔍 Semantic Category Gaps

Based on the evaluation of the 150-question bank, the following core knowledge gaps were identified in the RAG system:

### Gap 1: Faculty Directory Navigation & Capabilities
* **Failed Questions:**
  * `FAC014`: *Can I filter faculty by department?*
  * `FAC016`: *How detailed are faculty profiles at DA-IICT?*
  * `FAC019`: *Is faculty profile information publicly accessible?*
  * `FAC020`: *Where is the main faculty database maintained?*
* **Failure Reason:** The RAG system retrieves individual faculty profile files but has no meta-information about the web interface's directory capabilities (such as filtering by department, API access, or update schedules).
* **Missing Knowledge:** Documentation explaining the features, search filters, structure, and backend database of the official DA-IICT Faculty Directory.
* **Required Source:** DA-IICT Webmaster or IT administration guide.
* **Priority:** Medium

### Gap 2: Dean of Faculty Affairs Appointment & Office Details
* **Failed Questions:**
  * `FAC027`: *How is the Dean Faculty appointed?*
  * `FAC029`: *Where is the Dean Faculty office located?*
* **Failure Reason:** The RAG system retrieved the Dean's page, but the page only lists the Dean's name and general welcome message. Details on office room numbers and appointment processes are absent.
* **Missing Knowledge:** Specific office location (room number/building) of the Dean of Faculty Affairs and the selection/appointment criteria.
* **Required Source:** Faculty Handbook or Administration Office.
* **Priority:** Medium

### Gap 3: Adjunct & International Faculty Selection & Roles
* **Failed Questions:**
  * `FAC031`: *What are adjunct faculty members?*
  * `FAC034`: *What is the role of adjunct faculty?*
  * `FAC035`: *Are adjunct faculty full-time employees?*
  * `FAC036`: *How are adjunct faculty selected?*
  * `FAC038`: *Where is international adjunct faculty information available?*
* **Failure Reason:** The RAG system retrieved historical annual reports or NAAC cycle documents containing noise, but failed to retrieve current active policies or pages clarifying the selection criteria and roles of adjunct faculty.
* **Missing Knowledge:** Clear, structured policy document on the appointment, criteria, expectations, and status of adjunct and international visiting faculty.
* **Required Source:** Registrar Office or Academic Dean policies.
* **Priority:** High

### Gap 4: Centralized Research Output and Searching
* **Failed Questions:**
  * `FAC044`: *Is there a database for faculty research output?*
  * `FAC045`: *Can I search faculty publications by name?*
  * `FAC048`: *Where is publication data stored?*
* **Failure Reason:** The system has individual profiles containing list of publications, but lacks information on whether a centralized library database (e.g., IRINS, Scopus, or a local library repository) is available for searching.
* **Missing Knowledge:** Guide on using the DA-IICT Library or institutional repository to search and browse publications.
* **Required Source:** DA-IICT Library guide or IRINS portal documentation.
* **Priority:** Medium

---

## 🛠️ Technical / Rate Limit Failures
* **Failed Questions:** `FAC058` to `FAC150` (mostly rate-limited).
* **Failure Reason:** The Groq API hit the Tokens Per Day (TPD) limit of `100,000` tokens for the `llama-3.3-70b-versatile` model during bulk sequential processing of large prompt contexts.
* **Missing Knowledge:** N/A (Technical limit of API keys).
* **Required Source:** Upgrade Groq key tier, implement local embedding models, or increase retry-backoff times with rate limit handling in the evaluator.
* **Priority:** High (Technical blocker)
