# DAU PWA Future Sources Plan

**Purpose:** This document outlines the strategic plan for future knowledge acquisition to patch the gaps identified in the current RAG pipeline. It identifies key personnel, administrative bodies, and technical integrations required to achieve comprehensive model accuracy.

---

### Integration 1: Real-Time Placement Logistics
* **Source Type:** System Integration / API
* **Person/Committee:** University IT Services / Placement Cell Tech Support
* **Information Required:** Read-only API access or daily webhook feeds containing live JAF submission deadlines, interview room allocations, company shortlists, and ongoing drive statuses.
* **Expected Outcome:** The model will be able to accurately answer time-sensitive, dynamic questions (e.g., "Which companies are visiting tomorrow?") without hallucinating or hitting out-of-scope guardrails.

### Integration 2: Student Preparation & Interview Experiences
* **Source Type:** Curated Knowledge Repository
* **Person/Committee:** Student Placement Committee (Deputy Conveners) / Alumni Association
* **Information Required:** Subjective preparation guides, domain-specific tech stack recommendations (ML, Frontend, UI/UX), and historical interview transcripts for major companies (Google, DE Shaw, Sprinklr).
* **Expected Outcome:** A new set of Markdown files specifically dedicated to peer-to-peer advice, bridging the gap between official policy and actual student experience.

### Integration 3: Placement Brochure Data Restructuring
* **Source Type:** Structured Data Extraction
* **Person/Committee:** Data Engineering Team (Team A) / Placement Cell Data Analyst
* **Information Required:** The 2024-25 Placement Brochure must be re-processed. High-density tables containing median CTCs, highest stipends, and company categories must be manually extracted into pure CSV or JSON formats rather than standard Markdown chunking.
* **Expected Outcome:** Immediate resolution of the 45+ retrieval failures related to exact financial statistics and historical placement metrics.

### Integration 4: Portal ERP Mechanics
* **Source Type:** Internal Technical Documentation
* **Person/Committee:** ERP Development Team / Placement Office Administration
* **Information Required:** Technical FAQs explaining how the placement portal automatically fetches CGPAs, integrates with Mettl assessment scores, and verifies digital resumes.
* **Expected Outcome:** Reduction in technical support tickets, as the RAG model will successfully explain portal mechanics to confused students.

### Integration 5: Disciplinary & Audit Policies
* **Source Type:** Administrative Policy Documents
* **Person/Committee:** Disciplinary Action Committee (DAC) / Placement Cell Convenor (e.g., Mr. Jevik Rakholiya)
* **Information Required:** Official documentation on the zero-tolerance policy, the role of PIAAC vs DAC, and access to the public-facing summaries of the IPRS audit reports.
* **Expected Outcome:** Comprehensive and legally accurate answers to student questions regarding placement rule violations and official auditing standards.
