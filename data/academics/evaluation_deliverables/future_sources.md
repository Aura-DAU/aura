# Academics Cluster - Future Sources Plan

**Purpose:** Plan future knowledge acquisition for the missing topics identified in our `coverage_map.md` (primarily Layer 3 and Layer 4 items).

> [!IMPORTANT]
> **High Priority Action:** The Layer 4 System Integrations (ERP and LMS) require immediate administrative approval from IT Services. Without these APIs, the AI will not be able to answer dynamic student queries about their attendance, grades, or active Moodle assignments.

---

## Action Plan Table

| ID | Priority | Source Type | Person / Committee | Information Required | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | High | Dynamic Integration | Academic Office | Live API access or regular CSV exports of current semester timetable. | Automated script to update `current_timetable.md` weekly. |
| **2** | High | System API | IT Services / SysAdmin | API documentation for the university ERP system (Grades, Attendance). | Backend service fetching real-time grades for authenticated users. |
| **3** | High | System API | Moodle Administrator | Access tokens to index course-specific announcements and assignments. | Automated indexing of Moodle data into Pinecone. |
| **4** | Medium | Human Input (Survey) | Dept Heads & Senior Faculty | Recommended electives, prerequisites insights, common pitfalls for core subjects. | New markdown documents detailing faculty recommendations per subject. |
| **5** | Medium | Human Input (Survey) | Student Academic Council | Reviews of electives, workload estimates, career relevance. | `elective_recommendations.md` (Student-sourced). |
| **6** | Low | Committee Policy | Academic Advising Committee | SOPs for mentorship, advice given to underperforming students. | `academic_advising_guidelines.md` |

---

> [!TIP]
> **Next Steps:** Assign the IDs above to specific team members in your project management tool to track progress on acquiring this data.
