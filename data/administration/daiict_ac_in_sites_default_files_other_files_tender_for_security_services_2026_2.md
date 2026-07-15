---
title: "Document"
url: "https://www.daiict.ac.in/sites/default/files/other-files/Tender-for-Security-Services_2026-27_V1_200326.pdf"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "PDF"
pdf_name: "Document"
last_fixed: "2026-07-04"
fixes_applied: ['OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Document structuring assistant for AURA RAG system at DAU.
   - **Input:** Raw PDF-extracted text for a tender document ("Tender for Security Services, DAU, Gandhinagar").
   - **Rules:**
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens (~200 words). Split if needed.
     - Preserve ALL numbers, names, dates, codes, amounts exactly.
     - Convert garbled tables to proper Markdown tables.
     - Remove repeated headers, footers, page numbers, horizontal rules, control chars, OCR noise.
     - Fix obvious OCR typos only if 100% certain.
     - Use `[illegible]` for unreadable parts.
     - Do NOT add content.
   - **Raw Text Analysis:**
     - Title: "TENDER Security Service, DAU, Gandhinagar"
     - Tender No: Tender/Admin/Security/26-27/001
     - Date: 20.03.2026
     - Contact: Mr. Kirit Pandya, Manager Administration, +91 93270 43616, 079-68261592
     - Timing: Mon-Fri, 10:00-17:00
     - Last date: 02.04.2026 up to 11:00 hrs.
     - Submission address: Head HR & Admin., Dhirubhai Ambani University, Gandhinagar
     - Annexures listed: 1 to 4
     - Footer repeats: "DA-IICT Road, Gandhinagar, Gujarat, India 382007 T: +91 79 6826 1700 I info@dau.ac.in I www.dau.ac.in" (Remove)
     - Horizontal rules: `_______________________________________________________________________________________` (Remove)
     - Content is mostly Annexure 1: General Terms & Conditions.
     - Structure needed:
       - H1: Tender for Security Services, DAU, Gandhinagar
       - H2: Tender Details
       - H2: Annexure 1: General Terms & Conditions
         - H3: Bid Terms & Conditions
         - H3: Tender Fee & Bank Details
         - H3: Security Deposit
         - H3: Rejection & Award of Contract
         - H3: General Terms and Conditions
         - H3: Labour Laws and Workmen Compensation Act
         - H3: Scope of Contractor
         - H3: Licenses & Certificates
         - H3: Uniform and PPE
         - H3: Minimum Requirements
         - H3: Additional Jobs, Termination, Defective Work & Disputes
     - Check token/word limits per section: I'll split carefully to keep each ~200 words.
     - Preserve exact data: Dates, amounts, names, bank details, etc.
     - Fix OCR: "Univeristy" -> "University", "liasioning" -> "liaisoning", "off load or total quantum" -> likely "offload or reduce total quantum", but I'll stick close to original or fix obvious ones. "bind" at the end is cut off, I'll leave as is or add `[illegible]` if needed, but it says "final and bind" -> probably "binding". I'll keep "final and binding" or just "final and bind" as per rule 9 (fix only if 100% certain). I'll keep "final and binding" as it's standard, but rule says preserve exactly. I'll stick to "final and binding" or just "final and bind". I'll use "final and binding" as it's a clear OCR cutoff. Actually, I'll just write "final and binding" or leave as "final and bind". I'll follow rule 9 strictly.
     - Table conversion: Bank details are listed line by line. I'll convert to a markdown table.
     - Remove footers/repeated headers.
     - Structure carefully.

2.  **Draft Construction (Mental Refinement):**
   *H1*: # Tender for Security Services, DAU, Gandhinagar
   *H2*: ## Tender Details
   *Content*: Tender No: Tender/Admin/Security/26-27/001 | Date: 20.03.2026 | DAU Contact Person: Mr. Kirit Pandya, Manager Administration | (M) +91 93270 43616 | Phone: 079-68261592 | Contact Timing: Monday to Friday, 10:00 Hrs to 17:00 Hrs | Last date of Submission of Tender: 02.04.2026 up to 11:00 hrs. | Note: The Tender to be submitted in sealed envelope addressed to Head HR & Admin., Dhirubhai Ambani University, Gandhinagar. | Annexures: 1. General Terms & Conditions, 2. Primary Information of the Bidder, 3. Security Personnel Wages Calculation, 4. Experience and Financial details.
   *(Check length: ~70 words. Good.)*

   *H2*: ## Annexure 1: General Terms & Conditions
   *H3*: ### Bid Terms & Conditions
   *Content*: - The bidder should invariably submit bid documents in sealed covers.
   - All documents issued to tenderers for the purpose of tendering shall be submitted by him only duly filled in and signed on every page as a token of acceptance of conditions and completed in all respect.
   - Method of work, specifications, mode of measurements and other details wherever not mentioned should be followed as per Contract Administrator.
   - The contractor must study the scope of services etc. before quoting the rates.
   *(Check length: ~70 words. Good.)*

   *H3*: ### Tender Fee & Bank Details
   *Content*: The bidder will have to submit Non-refundable Bid Processing Fees of Rs.5900/- on or before date & hours of submission of bid in a sealed cover at Dhirubhai Ambani University. Tender Fee should be paid through NEFT/RTGS as per below bank details. The tender without tender fee will not considered.
   | Field | Details |
   |---|---|
   | Name of Account Holder | DHIRUBHAI AMBANI UNIVERSITY |
   | Bank Name & Branch | ICICI BANK GANDHINAGAR |
   | Account Number | 016501013975 |
   | IFSC CODE | ICIC0000165 |
   | City | GANDHINAGAR |
   | State/Province | GUJARAT |
   | Address of the Bank | PLOT NO. 315, SECTOR-16, NEAR GH-4 CIRCLE, GANDHINAGAR 382016. |
   | Telephone No. of the Bank | 23234252, 23234256 |
   | Country | INDIA |
   | Account Type | Savings |
   *(Check length: ~110 words. Good.)*

   *H3*: ### Security Deposit
   *Content*: 5% of total order value to be deposited with DAU in 7 working days after receipt of work order. The same amount will be returned in 30 days after completion / termination of contract period after deduction of dues if any. No interest shall be paid on Security Deposit amount. DAU reserves the right to encase or deducts any sum due to failure of any conditions of contract without reference to contractor.
   *(Check length: ~70 words. Good.)*

   *H3*: ### Rejection & Award of Contract
   *Content*: **Rejection of Bid:** Dhirubhai Ambani University reserves the right to reject any Bid, and the bidding process and reject all bids at any time prior to award of Contract, without thereby incurring any liability to the affected Bidder(s) or any obligation to inform the affected Bidder(s) of the grounds for such decision.
   **Award of Contract:** Award Criteria: The Criteria for selection will be the past and current experience of the contractor to provide security services in higher education institutions (universities) and competitive financial bid.
   *(Check length: ~80 words. Good.)*

   *H3*: ### General Terms and Conditions
   *Content*: - The Contractor will maintain the equipment and other properties of DAU in good condition. Damage to any equipment, appliances and other properties (both movable and immovable of DAU due to negligence. Commission /omission of the contractor or his employees or agents shall be brought to the notice of the DAU for recovery of such damages from the amounts payable to the Contractor.
   - The Contractor shall be responsible for boarding and lodging of their manpower with require safety, security and liasioning work.
   - Contractor shall make himself and their staff fully conversant with the nature of the organization (university with students and faculty members) and the type of job be carried out therein so that he clearly understands the scope of work and assess the requirement of resources required to perform the duty. The Contractor shall contact the Contract Administrator for this purpose.
   - DAU reserve the right to off load or total quantum of the job depending upon the exigencies.
   - There shall be no objection from the contractor for any other agencies working on the same site.
   - In case the Contractor fails to provide any services in time or fails to ensure the job carried out at the fullest satisfaction of the Contract Administrator, whose decision will be final and binding on the Contractor. The University has every rights to engage another agency or get the job done by employing any other Contractor and the charges for the same together with consequential expenses incurred / losses suffered by the University will be recovered from the Contractor.
   *(Check length: ~180 words. Good.)*

   *H3*: ### Labour Laws and Workmen Compensation Act
   *Content*: - The contractor shall follow the provisions of the labour laws and codes as amended from time to time and make payment of compensation in case of accidental injury during maintenance work in accordance with the provisions of WC Act. the contractor shall insure all of his workman under the Workmen Compensation Act by way by taking an Insurance Policy to cover himself against all claims and shall extend these legal heir within the specified time.
   - Contractor to follow all safety norms.
   - All statutory liabilities towards contractor’s employee shall be sole responsibility of the Contractor.
   *(Check length: ~90 words. Good.)*

   *H3*: ### Scope of Contractor
   *Content*: - To carry out the jobs in a manner as per instruction of Contract Administrator.
   - The CONTRACTOR shall also maintain required manpower for the purpose of replacement of guards and deploying competent guards in case of leave by the guards deployed. For the emergency calls from DAU. Emergency response system must be within 1 hour
   - CONTRACTOR shall deploy sufficient resources and shall make arrangement for effective supervision for the execution of the awarded jobs.
   - To keep vigil on, and to check, if required, all incoming and outgoing persons including CONTRACTORs employees and labours, visitors etc.To keep vigil on and to check if required, all incoming and outgoing materials, vehicles including cars, trucks, scooters, motor-cycles bicycles etc so as to ensure that there is no unauthorized entry or exit of men, materials and vehicles in the DAU’s premises.
   - To record and maintain the register of major and minor events occurring during the period of 24 hours and report same to the authorized officer of the DAU every day regularly in the form of daily report.
   - To maintain Registers & other documents for incoming and outgoing men, materials and vehicles etc. in such proforma as may prescribed by the DAU from time to time.
   - To inquire into any theft, pilferage, fire disobedience, rowdism, indiscipline, unauthorized activities and all other criminal activities in DAU’s premises and report the same to the authorized officer of the DAU and if require to lodge the further police complaints, if so desired by the DAU. To provide necessary law and order assistance to DAU in case of calamities
   - To carry out surprise checking personally by the CONTRACTOR or CONTRACTORs senior officers to ensure effective services by the security staff deployed by the CONTRACTOR in the DAU’s premises.
   - Pre-employment police verification of character and antecedents of the candidates for the employment in the DAU.
   - The CONTRACTOR shall rotate the security personnel deployed for the contract at suitable intervals or as and when suggested by the DAU.
   - Should have night vigilance system of deployed security officer / guard and any unwanted incident / report must be given in writing to the administrative officer on very next day
   *(Check length: ~230 words. Slightly over 200. I'll split it into two H3s: "Scope of Contractor (Part 1)" and "Scope of Contractor (Part 2)" or just "Scope of Contractor" and "Operational & Vigilance Requirements". Let's split logically.)*
   I'll split after the supervision point.
   *H3*: ### Scope of Contractor (Part 1)
   *Content*: - To carry out the jobs in a manner as per instruction of Contract Administrator.
   - The CONTRACTOR shall also maintain required manpower for the purpose of replacement of guards and deploying competent guards in case of leave by the
