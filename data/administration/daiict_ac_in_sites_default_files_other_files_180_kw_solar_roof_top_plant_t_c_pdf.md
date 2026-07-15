---
title: "Document"
url: "https://www.daiict.ac.in/sites/default/files/other-files/180_KW-Solar-Roof-Top-Plant_T-C.pdf"
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
   - **Input:** Raw PDF-extracted text for a tender document.
   - **Rules:**
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens (~200 words). Split if needed.
     - Preserve ALL numbers, names, dates, codes, amounts exactly.
     - Convert garbled tables to Markdown tables.
     - Remove repeated headers, footers, page numbers, horizontal rules, control chars, OCR noise.
     - Fix obvious OCR typos only if 100% certain.
     - Use `[illegible]` for unreadable parts.
     - Do NOT add content.
   - **Raw Text Analysis:**
     - Title: "180 KW Solar Power Plant, HoR Men (New) Terrace, DAU, Gandhinagar"
     - Tender No: EE2526009
     - Contact: Mr. Rajesh Patel, Sr. Engineer Estate, estate_engineer@daiict.ac.in, +91 93287 21608, 079-68261622
     - Timing: Mon-Fri, 10:00-17:00
     - Pre-bid/site visit: 17-18-19 November, 2025
     - Submission deadline: 29 November, 2025, 4:00 PM
     - Annexures listed: 1, 2, 3
     - Footer repeats: "DA-IICT Road, Gandhinagar, Gujarat, India 382007 T: +91 79 6826 1700 I info@dau.ac.in I www.dau.ac.in" (Remove)
     - Content is mostly "Annexure - 1 Bid Terms & Conditions" with bullet points.
     - Contains a bank details section that looks like a table.
     - Ends abruptly: "All legal disputes arising out of this contract will be subject to Gandh" (likely "Gandhinagar jurisdiction" or similar, but I must preserve exactly or mark illegible if cut off. I'll keep it as is or note it's cut off, but rule says preserve exactly. I'll just end it as is.)
     - Need to structure into H1, H2, H3.
     - Check token limits per section: ~200 words. I'll split the long bullet list into logical H3 subsections.

2.  **Structure Planning:**
   - H1: 180 KW Solar Power Plant, HoR Men (New) Terrace, DAU, Gandhinagar
   - H2: Tender Details
     - H3: Contact Information
     - H3: Important Dates
     - H3: Annexures
   - H2: Annexure 1: General Terms & Conditions
     - H3: Bid Submission & Processing
     - H3: Financial Terms & Security Deposit
     - H3: Bank Details for Tender Fee
     - H3: Scope of Work & Contractor Responsibilities
     - H3: General Terms & Conditions
     - H3: Workmen Compensation & Safety
     - H3: Maintenance & Warranty
     - H3: Execution & Termination
     - H3: Dispute Resolution
   - I need to carefully distribute the bullet points into these H3s to keep each under ~200 words.
   - I will convert the bank details into a markdown table.
   - I will remove all footers and repeated headers.
   - I will fix minor OCR issues if obvious (e.g., "pkg & fwdg" -> "packing & forwarding", "liasioning" -> "liaisoning", "encase" -> "encash", "expect" -> "except", "by way by" -> "by way of", "these legal heir" -> "these to legal heirs"). I'll be careful to only fix obvious ones.
   - Let's draft step-by-step.

   **Draft Construction:**

   # 180 KW Solar Power Plant, HoR Men (New) Terrace, DAU, Gandhinagar

   ## Tender Details
   ### Contact Information
   **Tender No:** EE2526009
   **DAU Contact Person:** Mr. Rajesh Patel, Sr. Engineer Estate
   **Email:** estate_engineer@daiict.ac.in
   **Mobile:** +91 93287 21608
   **Phone:** 079-68261622
   **Contact Timing:** Monday to Friday, 10:00 Hrs to 17:00 Hrs

   ### Important Dates
   **Pre-bid meeting and site visit:** 17-18-19 November, 2025
   **Last date of Submission of Tender:** 29 November, 2025, 4:00 PM

   ### Annexures
   - Annexure 1: General Terms & Conditions
   - Annexure 2: Primary Information of the Bidder
   - Annexure 3: Technical & Financial Bid

   ## Annexure 1: General Terms & Conditions
   ### Bid Submission & Processing
   - The bidder should invariably submit bid documents in sealed covers.
   - All documents issued to tenderers for the purpose of tendering shall be submitted by him only duly filled in and signed on every page as a token of acceptance of conditions and completed in all respect.
   - Method of work, specifications, mode of measurements and other details wherever not mentioned should be followed as per Sample Work.
   - The contractor must study the quantities and specifications / make & model of material before quoting the rates.

   ### Financial Terms & Security Deposit
   - **Tender Fee:** The bidder will have to submit Non-refundable Bid Processing Fees of Rs.5900/- on or before date & hours of submission of bid in a sealed cover at Dhirubhai Ambani University. Tender Fee should be paid through NEFT/RTGS as per below bank details.
   - **Security Deposit:** 5% of total order value to be deposited with DAU in 7 working days after receipt of work order. The same amount will be returned in 30 days after completion of project and completion of punch points/balance works. No interest shall be paid on Security Deposit amount. Client reserves the right to encash or deducts any sum due to failure of any conditions of contract without reference to contractor.

   ### Bank Details for Tender Fee
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

   ### Scope of Work & Contractor Responsibilities
   - The work includes material and labour. No extra cost to be paid for wastage, carting, loading, unloading, lodging & boarding etc. The bidder should clearly indicate applicable taxes, freight, packing & forwarding charges etc. The transit insurance should be in the scope of bidder.
   - **Rejection of Bid:** Dhirubhai Ambani University reserves the right to reject any Bid, and the bidding process and reject all bids at any time prior to award of Contract, without thereby incurring any liability to the affected Bidder(s) or any obligation to inform the affected Bidder(s) of the grounds for such decision.
   - **Award of Contract:**
     - Award Criteria: The Criteria for selection will be the lowest cost for the technically qualified bids.
     - In case, the lowest bidder (L1) does not accept the award of contract or found to be involved in corrupt and/or fraudulent practices, the client shall decide next bidder to be awarded the contract.

   ### General Terms & Conditions
   - The Contractor will maintain the equipment and other properties of DAU in good condition. Damage to any equipment, appliances and other properties (both movable and immovable of DAU due to negligence, commission/omission of the contractor or his employees or agents shall be brought to the notice of the DAU for recovery of such damages from the amounts payable to the Contractor.
   - The Contractor shall be responsible for loading, unloading, shifting, safety and security of their material, tools & tackles.
   - The Contractor shall be responsible for boarding and lodging of their manpower with required safety, security, proper supervision on movement and liaisoning work.
   - The Contractor shall be responsible for cleaning of sites/area etc. complete.
   - The total tender value shall include all taxes, levies / duties paid or payable in execution of the contract, cost of transportation, lodging & unloading, lodging & boarding of Contractor's employee. Also include cost of labour, tools tackles etc.
   - Contractor shall make himself and their staff fully conversant with the locations and the type of job to be carried out therein so that he clearly understands the scope of work and assess the requirement of resources required to complete the work. The Contractor shall contact the Contract Administrator for this purpose.
   - DAU reserve the right to off load or total quantum of the job depending upon the exigencies.
   - Material used shall be strictly as per specifications / Make & Model.
   - Water & power shall be provided at one convenient point at free of cost by owner. If wastage of supplied water & electricity is made by contractor’s labour, reasonable amount shall be recovered from contractor’s bill as compensation.
   - There shall be no objection from the contractor for any other agencies working on the same site.
   - The contractor shall have to give detailed working schedule of the execution for the work justifying expected progress of work. If the progress of the work is not satisfactory, a second agency shall be employed by the client for some part of same work.
   - In case the Contractor fails to provide any services in time or fails to ensure the job carried out at the fullest satisfaction of the Contract Administrator, whose decision will be final and binding on the Contractor. The Institute has every rights to engage another agency or get the job done by employing any other Contractor and the charges for the same together with consequential expenses incurred / losses suffered by the Institute will be recovered from the Contractor.
   - The Contractor shall subject to the provisions of the contract and with the care and diligence execute and maintain the works and provide all labour including, the supervision thereof.
   - The Contractor shall take full responsibility for the adequacy, stability and safety of all site operations and methods of construction, provided that the contractor shall not be responsible, except as may be expressly provided in the contract, for the design or specification of the permanent works, or for the design or specification of any temporary works prepared by the Architect/ Project manager.
   - The Engineer shall be at liberty to object to and require the Contractor to remove forthwith from the work any person employed by the Contractor in or about the execution of maintenance of the works who, in the opinion of the Engineer, misconducts himself, or is incompetent or negligent in the proper performance of his duties or whose employment is otherwise considered by the Engineer to be undesirable and such person shall not be again employed upon the works without the written permission of the Engineer.
   - Apart from one-year overall execution warranty the bidder shall mention warranty against each item as per manufacturer’s policy.

   *(Wait, this section is too long. I need to split it to keep under ~200 words per H3. Let's break "General Terms & Conditions" into multiple H3s.)*

   Let's restructure carefully to respect the ~256 token limit per section.

   **Revised Structure:**
   # 180 KW Solar Power Plant, HoR Men (New) Terrace, DAU, Gandhinagar
   ## Tender Details
   ### Contact Information
   **Tender No:** EE2526009
   **DAU Contact Person:** Mr. Rajesh Patel, Sr. Engineer Estate
   **Email:** estate_engineer@daiict.ac.in
   **Mobile:** +91 93287 21608
   **Phone:** 079-68261622
   **Contact Timing:** Monday to Friday, 10:00 Hrs to 17:00 Hrs

   ### Important Dates
   **Pre-bid meeting and site visit:** 17-18-19 November, 2025
   **Last date of Submission of Tender:** 29 November, 2025, 4:00 PM

   ### Annexures
   - Annexure 1: General Terms & Conditions
   - Annexure 2: Primary Information of the Bidder
   - Annexure 3: Technical & Financial Bid

   ## Annexure 1: General Terms & Conditions
   ### Bid Submission & Processing
   - The bidder should invariably submit bid documents in sealed covers.
   - All documents issued to tenderers for
