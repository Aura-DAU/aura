# DAU PWA Knowledge Gaps

### Gap 1
* **Question:** Which companies are visiting the campus next week? / What is the JAF submission deadline for the upcoming Amazon drive? (19 related queries)
* **Failure Reason:** Source Data Missing (Model hit the out-of-scope guardrail because real-time data is not in the vector DB).
* **Missing Knowledge:** Real-time, dynamic placement logistics, current drive schedules, and live interview statuses.
* **Required Source:** Live API Integration or dynamic `Missing - Level 2` logistical updates.
* **Priority:** High

### Gap 2
* **Question:** Which skills should I mainly target to apply for a machine learning internship? / What is the basic linked list STL syntax in C++? (15 related queries)
* **Failure Reason:** Expected source missing from retrieved context (The DB does not contain specific coding syntax or subjective career advice).
* **Missing Knowledge:** Technical preparation guides, past interview experiences, and specific resume-building strategies.
* **Required Source:** Mentorship guides, alumni experience repositories, or `Missing - Level 3` preparation materials.
* **Priority:** Medium

### Gap 3
* **Question:** Does the placement portal automatically fetch my CGPA from the university ERP? (12 related queries)
* **Failure Reason:** Source Data Missing (Model hit guardrail).
* **Missing Knowledge:** Technical details about how the internal placement portal and university ERP systems operate behind the scenes.
* **Required Source:** Portal technical documentation or `Missing - Level 4` internal system guides.
* **Priority:** Low

### Gap 4
* **Question:** What is the median CTC for the university? / What was the highest monthly stipend offered for an internship? (45 related queries)
* **Failure Reason:** Expected source missing from retrieved context (The DB failed to reliably pull the Placement Brochure).
* **Missing Knowledge:** Exact financial figures, stipends, cutoff criteria, and eligibility rules specific to the current placement year.
* **Required Source:** `daiict_ac_in_sites_default_files_other_files_placement_brochure_2025_26_pdf.md` (Currently present but failing retrieval chunking/embedding limits).
* **Priority:** Critical

### Gap 5
* **Question:** Where can I find the IPRS audit reports for UG placements? / Who handles disciplinary issues during the placement process? (10 related queries)
* **Failure Reason:** Expected source missing from retrieved context.
* **Missing Knowledge:** Specific internal placement cell hierarchy, disciplinary policies, and exact audit report locations.
* **Required Source:** `placement_cell.md`
* **Priority:** High

### Gap 6
* **Question:** Which four major tech companies shared the first day slot? (6 related queries)
* **Failure Reason:** Source Data Missing.
* **Missing Knowledge:** Historical news archives regarding specific past placement drives (like the Google first-time drive).
* **Required Source:** `da_iict_extends_its_record_of_excellent_placements_google_opens_the_drive_for_the_first_time.md`
* **Priority:** Low
