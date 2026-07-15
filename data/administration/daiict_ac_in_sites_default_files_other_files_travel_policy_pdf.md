---
title: "Policies/Travel Policy"
url: "https://www.daiict.ac.in/sites/default/files/other-files/Travel-Policy.pdf"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "PDF"
pdf_name: "Policies/Travel Policy"
last_fixed: "2026-07-04"
fixes_applied: ['OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Document structuring assistant for AURA RAG system at DAU.
   - **Input:** Raw PDF-extracted text for a "Travel Policy" document.
   - **Rules:**
     1. Output ONLY markdown body.
     2. H1 for title.
     3. H2 for major sections.
     4. H3 for subsections.
     5. Each H2/H3 section ~256 tokens max. Split if needed.
     6. Preserve ALL numbers, names, dates, codes, amounts exactly.
     7. Convert garbled tables to proper Markdown tables.
     8. Remove headers, footers, page numbers, horizontal rules, control chars, OCR noise.
     9. Fix obvious OCR typos only if 100% certain.
     10. Use [illegible] for unreadable values.
     11. Do NOT add content.
   - **Raw Text Analysis:**
     - Title: Policy on Reimbursement of Travel-related Expenses
     - Sections: Sanctioning Authorities and Prior Approval, Allowed Types of Travel, Daily Allowance Limits, Reimbursement Claims, International Travel, Travel Allowance (TA) & Daily Allowance (DA) Claim Form.
     - Contains tables for Sanctioning Authorities, Allowed Types of Travel, Daily Allowance Limits, Reimbursement Claims, and a Claim Form.
     - Some OCR noise/garbling in tables (e.g., "Rs. 9,00/-", "Easter Europe", "T ravel", formatting issues).
     - Page numbers: "Page 1 of 3", "Page 2 of 3", "Page 3 of 3".
     - Footer/Note: "This is issued with the approval of Director General", "Effective date...", "Note: Travel Settlements Form attached herewith:"
     - Need to structure carefully, split large sections if needed, fix tables, preserve data.

2.  **Process & Structure (Mental Draft):**
   *H1:* # Policy on Reimbursement of Travel-related Expenses
   *H2:* ## Sanctioning Authorities and Prior Approval
   *Content:* Prior approval is required for any official travel, including the travel to attend a conference, technical seminar/workshop, meetings for sponsored research projects, etc. An employee shall request prior approval from their sanctioning authority via email before planning for the travel. Travel reimbursement request shall not be processed in absence of this prior approval.
   *H3:* ### Approving Authorities
   *Table:*
   | ID | Employee Category | Purpose of Travel | Approving Authority |
   |---|---|---|---|
   | 1 | Faculty | Research related | Dean Research |
   | 2 | Faculty | Institute and Academics related | Dean Faculty |
   | 3 | Research Associates | Sponsored research related | Principal Investigator, followed by Dean Research |
   | 4 | Teaching Assistants | Academics related | Dean AP |
   | 5 | Administrative Staff | Institute related | Reporting Manager/Head – HR & Admin. followed by Executive Registrar |
   *(Note: Fixed table structure from raw text. Raw had "ID Employee Category Purpose of Travel Approving Authority" then rows. I'll align it properly.)*

   *H2:* ## Allowed Types of Travel
   *Content:* The allowed mode of travel shall be as per the following table:
   *Table:*
   | Designation | Air | Rail | Road |
   |---|---|---|---|
   | Faculty | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-A) | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-B) | Economy Class | AC 2-tier Class | AC Taxi |
   | Research Associates, Project Personnel, Teaching Assistant | AC 3-tier class | AC Taxi / AC Bus | *(Wait, raw says "Research Associates, AC 3-tier class AC Taxi / AC Bus Project Personnel, Teaching Assistant". This is garbled. Let's parse carefully:)*
   Raw:
   Research Associates, AC 3-tier class AC Taxi / AC Bus
   Project Personnel,
   Teaching Assistant
   Staff: Group C or D 2nd AC / AC Chair Car Taxi / Bus
   Let's reconstruct based on standard policy tables:
   | Designation | Air | Rail | Road |
   |---|---|---|---|
   | Faculty | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-A) | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-B) | Economy Class | AC 2-tier Class | AC Taxi |
   | Research Associates, Project Personnel, Teaching Assistant | AC 3-tier class | AC Taxi / AC Bus | *(Wait, the raw text has "AC 3-tier class" under Rail? Actually, it says "Research Associates, AC 3-tier class AC Taxi / AC Bus Project Personnel, Teaching Assistant". This is messy. I will format it as best as possible preserving exact text but structuring it logically.)*
   Let's look at the raw again:
   "Research Associates, AC 3-tier class AC Taxi / AC Bus
   Project Personnel,
   Teaching Assistant
   Staff: Group C or D 2nd AC / AC Chair Car Taxi / Bus"
   I'll map it to:
   | Designation | Air | Rail | Road |
   |---|---|---|---|
   | Faculty | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-A) | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-B) | Economy Class | AC 2-tier Class | AC Taxi |
   | Research Associates, Project Personnel, Teaching Assistant | AC 3-tier class | AC Taxi / AC Bus | *(Wait, Air is missing for these? The raw says "Research Associates, AC 3-tier class AC Taxi / AC Bus". It might mean Rail: AC 3-tier, Road: AC Taxi/AC Bus. I'll keep it close to raw but structured.)*
   Actually, I'll just format exactly as the columns appear:
   | Designation | Air | Rail | Road |
   |---|---|---|---|
   | Faculty | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-A) | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-B) | Economy Class | AC 2-tier Class | AC Taxi |
   | Research Associates, Project Personnel, Teaching Assistant | AC 3-tier class | AC Taxi / AC Bus | *(I'll leave Air blank or put [illegible] if unsure, but I'll stick to raw: "AC 3-tier class" under Rail, "AC Taxi / AC Bus" under Road. I'll adjust to match columns.)*
   Let's reconstruct carefully:
   | Designation | Air | Rail | Road |
   |---|---|---|---|
   | Faculty | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-A) | Economy Class | AC First Class | AC Taxi |
   | Staff (Group-B) | Economy Class | AC 2-tier Class | AC Taxi |
   | Research Associates, Project Personnel, Teaching Assistant | AC 3-tier class | AC Taxi / AC Bus | *(Wait, the raw has "AC 3-tier class" then "AC Taxi / AC Bus". I'll put AC 3-tier class in Rail, AC Taxi/AC Bus in Road. Air is blank.)*
   | Staff: Group C or D | 2nd AC / AC Chair Car | Taxi / Bus | *(Wait, 2nd AC is Rail. Taxi/Bus is Road. Air is blank.)*
   I will format it exactly as a 4-column table, filling blanks where appropriate, preserving text.

   *H3:* ### Local Conveyance & Private Vehicle Rules
   1. The journey from airport to hotel or from hotel to venue, the local conveyance will be paid as per the car/taxi/autorickshaw mentioned above. The maximum ceiling for the local conveyance per trip will be Rs. 5000/-.
   2. For the travel by air, train or taxi, the reimbursement will be processed on the basis of the submitted receipts of the fare.
   3. If a DAU employee is traveling by their own private vehicle, the employee (i) shall specifically obtain approval of this mode of travel, and (ii) shall be reimbursed at the rate of Rs. 20 per kilometre. The receipts will not be required.

   *H2:* ## Daily Allowance Limits
   *H3:* ### Allowance Rates
   *Table:*
   | Designation | Hotel Accommodation per day (Metro Cities) | Hotel Accommodation per day (Non-Metro Cities) | Food per Day (with Receipts) | DA Rate without the Receipts |
   |---|---|---|---|---|
   | Faculty & Staff (Group-A) | Rs. 10,000/- | Rs. 7,500/- | Rs. 3,000/- | Rs. 1,200/- |
   | Staff (Group-B) | Rs. 7,000/- | Rs. 4,500/- | Rs. 2,000/- | Rs. 9,00/- |
   | Research Associates / Project Personnel / Teaching Assistant | Rs. 5,500/- | Rs. 3,000/- | Rs. 1,500/- | Rs. 9,00/- |
   | Staff (Group-C/D) | Rs. 5,500/- | Rs. 3,000/- | Rs. 1,500/- | Rs. 9,00/- |
   *(Note: Raw has "Rs. 9,00/-" which is likely a typo for 900/-, but rule 6 says preserve ALL numbers exactly. I will keep "Rs. 9,00/-" as is, or fix to Rs. 900/-? Rule 9 says fix obvious OCR typos only if 100% certain. "9,00/-" is clearly 900/-. I'll keep it as Rs. 900/- or preserve exactly? I'll preserve exactly: Rs. 9,00/- to be safe, or fix to Rs. 900/- as it's obvious. I'll stick to exact: Rs. 9,00/-)*
   Actually, I'll format the table exactly as the raw columns:
   | Designation | Hotel Accommodation per day (Metro Cities) | Hotel Accommodation per day (Non-Metro Cities) | Food per Day (with Receipts) | DA Rate without the Receipts |
   |---|---|---|---|---|
   | Faculty & Staff (Group-A) | Rs. 10,000/- | Rs. 7,500/- | Rs. 3,000/- | Rs. 1,200/- |
   | Staff (Group-B) | Rs. 7,000/- | Rs. 4,500/- | Rs. 2,000/- | Rs. 9,00/- |
   | Research Associates / Project Personnel / Teaching Assistant | Rs. 5,500/- | Rs. 3,000/- | Rs. 1,500/- | Rs. 9,00/- |
   | Staff (Group-C/D) | Rs. 5,500/- | Rs. 3,000/- | Rs. 1,500/- | Rs. 9,00/- |

   *H3:* ### Allowance Notes
   1. Hotel accommodation includes incidentals like laundry, telephone, internet, wifi or any other facilities used at the hotel.
   2. Payment for tips and hard drinks are not reimbursable.
   3. Daily Allowance without bills / receipts will be admissible only if there is no claim towards actual for hotel or food.
   4. In case the actual expenditure exceeds the approved limits as above, special approval of the Director is required for reimbursement.

   *H2:* ## Reimbursement Claims
   *H3:* ### Documentation Requirements
   | Mode of Travel | Requirement |
   |---|---|
   | By air | Boarding pass (if tickets are purchased by self) & air-ticket |
   | By train | Train ticket/ticket number, train number, class of travel |
   | By public transport, Taxi | Ticket, Invoice |

   *H3:* ### Claim Submission Rules
   1. The claim for reimbursement of travel expenses incurred has to be submitted within 3 months from the last date of return journey, failing which the amount of advance shall be recovered from the salary. If the claim is not submitted within 3 months, then the same will require approval from the sanctioning authority.
   2. In case of air or rail booking through Institute’s travel agents, the bills must be forwarded to the account section through the Administrative Section only.
   3. The following charges in respect of travel are reimbursable:
      a. Reservation charges for seat/sleeper berth
      b. Tatkal Seva charges.
      c. Internet, e-ticketing charges for the tickets booked through the website of Indian Railways
      d. Agency charges by the traveller’s service agents recognized by the
