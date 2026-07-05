---
title: "Document"
url: "https://www.daiict.ac.in/sites/default/files/other-files/Washroom-renovation-of-Students-Mess_TandC_260925.pdf"
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
   - **Input:** Raw PDF-extracted text for a tender document titled "Washroom renovation of Student’s Mess, DAU, Gandhinagar".
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
     - Title: TENDER Washroom renovation of Student’s Mess, DAU, Gandhinagar
     - Tender No: EE2526007
     - Contact: Mr. Rajesh Patel, Sr. Engineer Estate, email, phone, timing.
     - Dates: Pre-bid meeting & Site visit: 01.10.2025 at 10:00 A.M. Last date: 08.10.2025 up to 11:00 hrs.
     - Annexures listed.
     - Footer repeated multiple times: "DA-IICT Road, Gandhinagar, Gujarat, India 382007 T: +91 79 6826 1700 I info@dau.ac.in I www.dau.ac.in"
     - Annexure - 1: Bid Terms & Conditions (bullet points)
     - Bank details table-like structure.
     - More terms & conditions.
     - Ends abruptly: "The contractor will be submitted running account bill for the work completed with mea" (cut off). I'll preserve it as is or note it's cut off, but rule says preserve exactly. I'll just end it there.
     - Need to structure into H1, H2, H3.
     - Split long sections to keep ~200 words each.
     - Convert bank details to a table.
     - Remove footers and horizontal rules.
     - Fix minor OCR/formatting issues (e.g., "pkg & fwdg" -> "packing & forwarding", "liasioning" -> "liaisoning", "expect as may be" -> "except as may be", "mea" -> likely "mea" is cut off, I'll leave as is or fix to "mea" but rule says preserve exactly. I'll keep "mea" as is since it's cut off).
     - Check token/word limits per section. I'll split the long list of terms into logical H3 subsections.

2.  **Structure Planning:**
   - H1: TENDER: Washroom renovation of Student’s Mess, DAU, Gandhinagar
   - H2: Tender Details
     - H3: Contact Information
     - H3: Important Dates
     - H3: Annexures
   - H2: Annexure 1: General Terms & Conditions
     - H3: Submission & Documentation Requirements
     - H3: Tender Fee & Security Deposit
     - H3: Bank Details for Tender Fee
     - H3: Scope of Work & Cost Inclusions
     - H3: Bid Rejection & Award Criteria
     - H3: Contractor Responsibilities & Site Management
     - H3: Warranty, Maintenance & Safety
     - H3: Termination, Defects & Disputes
     - H3: Payment Terms
   - I need to ensure each H2/H3 section is ~200 words max. I'll carefully split the bullet points.

3.  **Draft Generation (Mental Refinement):**
   *(H1)* # TENDER: Washroom renovation of Student’s Mess, DAU, Gandhinagar
   *(H2)* ## Tender Details
   *(H3)* ### Contact Information
   Tender No: EE2526007
   DAU Contact Person: Mr. Rajesh Patel, Sr. Engineer Estate
   Email: estate_engineer@dau.ac.in
   Mobile: +91 93287 21608
   Phone: 079-68261622
   Contact Timing: Monday to Friday, 10:00 Hrs to 17:00 Hrs

   *(H3)* ### Important Dates
   Pre-bid meeting & Site visit: 01.10.2025 at 10:00 A.M.
   Last date of Submission of Tender: 08.10.2025 up to 11:00 hrs.

   *(H3)* ### Annexures
   - Annexure 1: General Terms & Conditions
   - Annexure 2: Primary Information of the Bidder
   - Annexure 3: Technical & Financial Bid
   - Annexure 4: Make and Model List
   - Annexure 5: Drawing

   *(H2)* ## Annexure 1: General Terms & Conditions
   *(H3)* ### Submission & Documentation Requirements
   - The bidder should invariably submit bid documents in sealed covers.
   - All documents issued to tenderers for the purpose of tendering shall be submitted by him only duly filled in and signed on every page as a token of acceptance of conditions and completed in all respect.
   - Method of work, specifications, mode of measurements and other details wherever not mentioned should be followed as per EIC.
   - The contractor must study the quantities and specifications / make & model of material before quoting the rates.

   *(H3)* ### Tender Fee & Security Deposit
   - **Tender Fee:** The bidder will have to submit Non-refundable Bid Processing Fees of Rs.5900/- on or before date & hours of submission of bid in a sealed cover at Dhirubhai Ambani University. Tender Fee should be paid through NEFT/RTGS as per below bank details. The tender without tender fee will not considered.
   - **Security Deposit:** 5% of total order value to be deposited with DAU in 7 working days after receipt of work order. The same amount will be returned in 30 days after completion of project and completion of punch points/balance works. No interest shall be paid on Security Deposit amount. Client reserves the right to encase or deducts any sum due to failure of any conditions of contract without reference to contractor.

   *(H3)* ### Bank Details for Tender Fee
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

   *(H3)* ### Scope of Work & Cost Inclusions
   - The work includes material and labour. No extra cost to be paid for wastage, carting, loading, unloading, lodging & boarding etc. The bidder should clearly indicate applicable taxes, freight, packing & forwarding charges etc. The transit insurance should be in the scope of bidder.
   - The total tender value shall include all taxes, levies / duties paid or payable in execution of the contract. cost of transportation, lodging & unloading, lodging & boarding of Contractor's employee. Also include cost of labour, tools tackles etc.
   - Water & power shall be provided at one convenient point at free of cost by owner. If wastage of supplied water & electricity is made by contractor’s labour, reasonable amount shall be recovered from contractor’s bill as compensation.

   *(H3)* ### Bid Rejection & Award Criteria
   - **Rejection of Bid:** Dhirubhai Ambani University reserves the right to reject any Bid, and the bidding process and reject all bids at any time prior to award of Contract, without thereby incurring any liability to the affected Bidder(s) or any obligation to inform the affected Bidder(s) of the grounds for such decision.
   - **Award of Contract:**
     - Award Criteria: The Criteria for selection will be the lowest cost for the technically qualified bids.
     - In case, the lowest bidder (L1) does not accept the award of contract or found to be involved in corrupt and/or fraudulent practices, the client shall decide next bidder to be awarded the contract.

   *(H3)* ### Contractor Responsibilities & Site Management
   - The Contractor will maintain the equipment and other properties of DAU in good condition. Damage to any equipment, appliances and other properties (both movable and immovable of DAU due to negligence. Commission /omission of the contractor or his employees or agents shall be brought to the notice of the DAU for recovery of such damages from the amounts payable to the Contractor.
   - The Contractor shall be responsible for loading, unloading, shifting, safety and security of their material, tools & tackles.
   - The Contractor shall be responsible for boarding and lodging of their manpower with require safety, security, proper supervision on movement and liaisoning work.
   - The Contractor shall be responsible for cleaning of sites/area etc. complete.
   - Contractor shall make himself and their staff fully conversant with the locations and the type of job be carried out therein so that he clearly understands the scope of work and assess the requirement of resources required to complete the work. The Contractor shall contact the Contract Administrator for this purpose.
   - DAU reserve the right to off load or total quantum of the job depending upon the exigencies.
   - Material used shall be strictly as per specifications / Make & Model.
   - There shall be no objection from the contractor for any other agencies working on the same site.
   - The contractor shall have to give detailed working schedule of the execution for the work justifying expected progress of work. If the progress of the work is not satisfactory, a second agency shall be employed by the client for some part of same work.
   - In case the Contractor fails to provide any services in time or fails to ensure the job carried out at the fullest satisfaction of the Contract Administrator, whose decision will be final and binding on the Contractor. The Institute has every rights to engage another agency or get the job done by employing any other Contractor and the charges for the same together with consequential expenses incurred / losses suffered by the Institute will be recovered from the Contractor.
   - The Contractor shall subject to the provisions of the contract and with the care and diligence execute and maintain the works and provide all labour including, the supervision thereof.
   - The Contractor shall take full responsibility for the adequacy, stability and safety of all site operations and methods of construction, provided that the contractor shall not be responsible, except as may be expressly provided in the contract, for the design or specification of the permanent works, or for the design or specification of any temporary works prepared by the Architect/ Project manager.
   - The Engineer shall be at liberty to object to and require the Contractor to remove forthwith from the work any person employed by the Contractor in or about the execution of maintenance of the works who, in the opinion of the Engineer, misconducts himself, or is incompetent or negligent in the proper performance of his duties or who employment is otherwise considered by the Engineer to be undesirable and such person shall not be again employed upon the works without the written permission of the Engineer.

   *(Check word count for above section)*: It's quite long. I need to split it further to comply with the ~200 words rule per H2/H3 section. Let's split "Contractor Responsibilities & Site Management" into two or three parts.

   Let's restructure carefully to ensure each section is ~200 words max.

   I'll split the long bullet list into:
   - H3: Property & Site Maintenance
   - H3: Work Schedule & Progress Monitoring
   - H3: Personnel & Safety Compliance
   - H3: Warranty, Maintenance & Safety
   - H3: Termination, Defects & Disputes
   - H3: Payment Terms

   Let's draft carefully.

   *(H3)* ### Property & Site Maintenance
   - The Contractor will maintain the equipment and other properties of DAU in good condition. Damage to any equipment, appliances and other properties (both movable and immovable of DAU due to negligence. Commission /omission of the contractor or his employees or agents shall be brought to the notice of the DAU for recovery of such damages from the amounts payable to the Contractor.
   - The Contractor shall be responsible for loading, unloading, shifting, safety and security of their material, tools & tackles.
   - The Contractor shall be responsible for boarding and lodging of their manpower with require safety, security, proper supervision on movement and liaisoning work.
   - The Contractor shall be responsible for cleaning of sites/area etc. complete.
   - Contractor shall make himself and their staff fully conversant with the locations and the type of job be carried out therein so that he clearly understands the scope of work
