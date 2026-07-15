---
title: "Courses Through CEP & AIP/Course Plan under CEP form pdf"
url: "https://www.daiict.ac.in/sites/default/files/other-files/Course-Plan-Proposal-under-CEP.pdf"
category: "academics"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "PDF"
pdf_name: "Courses Through CEP & AIP/Course Plan under CEP form pdf"
last_fixed: "2026-07-04"
fixes_applied: ['OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Document structuring assistant for AURA RAG system at DAU.
   - **Input:** Raw PDF-extracted text for a "Course Plan Proposal under CEP" form.
   - **Rules:** 
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens (~200 words). Split if needed.
     - Preserve all numbers, names, dates, codes, amounts exactly.
     - Convert garbled tables to proper Markdown tables.
     - Remove headers, footers, page numbers, horizontal rules, control chars, OCR noise.
     - Fix obvious OCR typos only if 100% certain.
     - Use `[illegible]` for unreadable parts.
     - Do NOT add content.
   - **Raw Text Analysis:** It's a form/template for proposing a course under CEP (Continuing Education Program). It has sections A through H, plus tables for revenue/expenses, surplus sharing, and signature blocks. The text is mostly clean but formatted as a form with checkboxes and lines. I need to structure it logically into Markdown.

2.  **Map to Structure:**
   - H1: Course Plan Proposal under CEP
   - H2: A. Basic Information
   - H3: Course Details & Modality
   - H3: Anchors & Instructors
   - H3: Schedule & Participants
   - H2: B. Program Schedule
   - H2: C. Lab and Infrastructure Requirements
   - H2: D. Final Examination Schedule
   - H2: E. Teaching-Assistant Office Hour Schedule
   - H2: F. Certificate Type
   - H2: G. Course Notes
   - H2: H. Commercial Aspects and Revenue
   - H3: Revenue Table
   - H3: Expenses Table
   - H3: Surplus Distribution
   - H2: Approval & Signatures
   - H3: Faculty Declaration
   - H3: CEP Office Use

   I need to ensure each section is concise and fits the token limit. I'll convert the form fields into a clean list/table format where appropriate, preserving all original labels.

3.  **Process Section by Section (Mental Refinement):**

   *Title:* # Course Plan Proposal under CEP

   *Preamble:* Please see CEP Policy Document. [Checkboxes for Conference, Short-term Course, Workshop, Symposium, Seminar, Other]

   *Section A:* Basic Information
   - Date: ______________
   - Course Title: 
   - Course Objective: 
   - Course Modality: ☐ Online ☐ Offline ☐ Hybrid
   - Anchor 1: Name, Email, Phone No.
   - Anchor 2 (if any): Name, Email, Phone No., Affiliation
   - No. of additional instructors: (provide brief bio, and other relevant info)
   - Total lecture hours: 
   - Lab/Tutorial Lecture Hours: 
   - Course duration (in days): 
   - Tentative Dates, Day and Time: 
   - Expected number of participants: 
   - Targeted Audience: 
   - Registration Fee (per participant incl. GST): 

   *Section B:* Program Schedule
   - Table: Date | Instructors Name | Topic | Lecture Timing

   *Section C:* Lab and Infrastructure Requirements
   - List the specific requirements, including software, hardware, and other infrastructure necessary for the course.

   *Section D:* Final Examination Schedule (optional)
   - Provide details of the final examination schedule if applicable.

   *Section E:* Teaching-Assistant Office Hour Schedule (optional)
   - Table: Date | Instructor/TA/Staff Name | Tutorial/Lab Topics | Timing

   *Section F:* Certificate Type
   - Choose one: (a) Participation, (b) Pass/Fail, or (c) Grade.

   *Section G:* Course Notes
   - The final course plan must be submitted to the Continuing Education Program (CEP) office at least 45 days before the tentative course start date.
   - For offline CEP programs, scheduling should preferably align with vacation periods or extended breaks within the semester due to current infrastructure limitations. If the program is offered during working days, ensure it does not interfere with regular classes/labs.
   - Please note that any course must have at least two instructors.

   *Section H:* Commercial aspects and Revenue
   - Table 1: Revenue
   - Table 2: Expenses
   - Surplus sharing table
   - Note: It is the faculty anchor(s) responsibility to ensure that K is always positive.

   *Signatures:*
   - Declaration
   - Anchor's Signature & Date
   - CEP Office Remarks & Approvals

   I will format these carefully into Markdown, ensuring tables are properly aligned and all original text is preserved. I'll split Section H into subsections to keep token counts low. I'll convert the form fields into a clean structured list/table format as requested.

   Let's draft it out carefully.

   *Self-Correction/Verification during drafting:*
   - Check rule 5: Each H2/H3 section must fit within ~256 tokens. I'll keep them concise.
   - Check rule 7: Convert garbled table text into proper Markdown tables. The raw text has table-like structures for Revenue, Expenses, and Surplus. I'll format them properly.
   - Check rule 8: Remove repeated headers, page numbers, etc. None present.
   - Check rule 10: Use [illegible] if needed. Not needed here.
   - I will structure the form fields as a clean list or table under H3s to maintain readability and structure.

   Structure:
   # Course Plan Proposal under CEP
   ## A. Basic Information
   ### Course Details & Modality
   ### Anchors & Instructors
   ### Schedule & Participants
   ## B. Program Schedule
   ## C. Lab and Infrastructure Requirements
   ## D. Final Examination Schedule
   ## E. Teaching-Assistant Office Hour Schedule
   ## F. Certificate Type
   ## G. Course Notes
   ## H. Commercial Aspects and Revenue
   ### Revenue Breakdown
   ### Expenses Breakdown
   ### Surplus Distribution
   ## Approval & Signatures
   ### Faculty Declaration
   ### CEP Office Use

   I will now generate the markdown exactly matching this structure, preserving all original text verbatim where possible, and formatting tables correctly. I'll ensure no extra text is added. All checkboxes and form lines will be kept as is or formatted cleanly. I'll replace the long underscores with standard markdown formatting or keep them as placeholders. The prompt says "preserve ALL numbers, names, dates, course codes, amounts exactly". I'll keep the exact labels.

   Let's construct it. 
   I'll carefully map the raw text to the markdown structure.
   Table 1 (Revenue) and Table 2 (Expenses) need proper markdown table syntax.
   Surplus table also needs proper syntax.
   I'll make sure the formatting is strict.
   All good. Proceed. 
   Output matches the response. 
   Self-Correction/Refinement during thought: 
   The raw text has "Sr. No. Item Details" followed by numbered items. I'll format this as a clean list/table under H3s to avoid clutter. I'll keep the exact wording.
   I will ensure each section is under ~200 words.
   I'll output only the markdown body.
   Ready. 
   Generating. 
   [Output Generation] -> *Proceeds*
   *(Self-Correction/Verification during generation prep)*: 
   I need to make sure the tables are perfectly aligned. The raw text for Table 1 and 2 is a bit messy. I'll reconstruct them logically based on the raw text:
   Table 1: Revenue
   | Item | Expected Revenue Amount (INR) |
   |---|---|
   | Total Revenue from Registration (incl. GST) | |
   | Total Revenue from Sponsorship (incl. GST) | |
   | A: Total | |
   | B: Reduce GST (18%) | |
   | C: Net Amount (A - B) | |
   | D: Funding from Govt. or Other GST exempt Agency | |
   | E: Net Available Revenue (C + D) | |

   Table 2: Expenses
   | Item | Expected Expenses Budget (incl. of GST) (INR) |
   |---|---|
   | A. Institute Overhead (fixed) (10% of Net Available Revenue (Table1.E)) | |
   | B. Faculty Anchor/Proposer(s): (10% of Net Available Revenue (Table1.E)) | |
   | C. Remuneration of Experts and TA | |
   | D. Food | |
   | E. Travel | |
   | F. Accommodation | |
   | G. Stationeries and Registration Kit | |
   | H. Marketing: External Marketing Agency as per requirement (optional) | |
   | NT 1: Support given by CEP Office and Communication Office | |
   | I. Contingencies | |
   | J. Total Expected Expenditure Sum(A:I) | |
   | K. Surplus (Net available Revenue - Total Expected Expenditure) | |

   Surplus Table:
   | Settlement of the surplus amount | Institute share | Faculty Program Coordinator(s) share |
   |---|---|---|
   | Surplus < 3 lakhs | 20% | 80% |
   | Surplus between 3 - 5 lakhs | 30% | 70% |
   | Surplus > 5 lakhs | 50% | 50% |

   This matches the raw text structure perfectly. I will now assemble the full markdown. All rules checked. Output matches response.✅
   Proceeds. 
   [Output Generation] -> *Outputs exactly the markdown body as requested.* 
   *(Note: I will ensure no extra text, frontmatter, or explanations are included.)*
   All set. 
   [Output Generation] -> *Proceeds*
</think>

# Course Plan Proposal under CEP

Please see CEP Policy Document
☐ Conference ☐ Short-term Course ☐ Workshop ☐ Symposium ☐ Seminar ☐ Other

## A. Basic Information
**Date:** ______________

### Course Details & Modality
1. **Course Title:** 
2. **Course Objective:** 
3(i). **Course Modality:** ☐ Online ☐ Offline ☐ Hybrid

### Anchors & Instructors
3(ii). **Anchor 1:** Name: | Email: | Phone No: 
3(iii). **Anchor 2 (if any):** Name: | Email: | Phone No: | Affiliation: 
4. **No. of additional instructors:** (please provide brief bio, and other relevant info)

### Schedule & Participants
5. **Total lecture hours:** | **Lab/Tutorial Lecture Hours:** 
6. **Course duration (in days):** 
7. **Tentative Dates, Day and Time:** 
8. **Expected number of participants:** 
9. **Targeted Audience:** 
10. **Registration Fee (per participant incl. GST):** 

## B. Program Schedule
| Date | Instructors Name | Topic | Lecture Timing |
|---|---|---|---|
| | | | |

## C. Lab and Infrastructure Requirements
List the specific requirements, including software, hardware, and other infrastructure necessary for the course.

## D. Final Examination Schedule
Provide details of the final examination schedule if applicable.

## E. Teaching-Assistant Office Hour Schedule
| Date | Instructor/TA/Staff Name | Tutorial/Lab Topics | Timing |
|---|---|---|---|
| | | | |

## F. Certificate Type
Choose one: (a) Participation, (b) Pass/Fail, or (c) Grade.

## G. Course Notes
- The final course plan must be submitted to the Continuing Education Program (CEP) office at least 45 days before the tentative course start date.
- For offline CEP programs, scheduling should preferably align with vacation periods or extended breaks within the semester due to current infrastructure limitations. If the program is offered during working days, ensure it does not interfere with regular classes/labs.
- Please note that any course must have at least two instructors.

## H. Commercial Aspects and Revenue

### Revenue Breakdown
| Item | Expected Revenue Amount (INR) |
|---|---|
| Total Revenue from Registration (incl. GST) | |
| Total Revenue from Sponsorship (incl. GST) | |
| A: Total | |
| B: Reduce GST (18%) | |
| C: Net Amount (A - B) | |
| D: Funding from Govt. or Other GST exempt Agency | |
| E: Net Available Revenue (C + D) | |

### Expenses Breakdown
| Item | Expected Expenses Budget (incl. of GST) (INR) |
|---|---|
| A. Institute Overhead (fixed) (10% of Net Available Revenue (Table1.E)) | |
| B. Faculty Anchor/Proposer(s): (10% of Net Available Revenue (Table1.E)) | |
| C. Remuneration of Experts and TA | |
| D. Food | |
| E. Travel | |
| F. Accommodation | |
| G. Stationeries and Registration Kit | |
| H. Marketing: External Marketing Agency as per requirement (optional) | |
| NT 1: Support given by CEP
