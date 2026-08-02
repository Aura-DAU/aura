# RAG Detailed Evaluation Report
## Section 1: Numbers + Meta Data
- **Total Questions Processed**: 170
- **Valid Answers**: 138
- **Guardrail Triggers**: 32
- **Average Latency**: 9447.64 ms
- **Server Name**: AURA_FastAPI_Backend
- **Model**: aura-rag-pipeline
- **Endpoint**: http://10.100.97.71:8000/chat

## Section 2: Question Wise Breakdown
### Q00001: What are the basic eligibility criteria for admission into the B.Tech/M.Tech programs?
**Chatbot Answer**:
> The documents retrieved do not provide information about the eligibility criteria for admission into the B.Tech/M.Tech programs. They focus on the credit requirements and structure of the five-year dual degree program. For specific eligibility criteria, you may need to refer to the official university website or contact the admissions office for detailed information.

**Actual Answer (Expected)**:
> For B.Tech: passed 10+2 (or equivalent) with the minimum percentage prescribed by AICTE, including Mathematics, Physics and one of Chemistry/Bio-technology/Computer Science/Biology. M.Tech eligibility (e.g. GATE score, relevant bachelor's degree) is set separately per PG program page and not in this document.

**Meta Data**:
- Category: eligibility_criteria
- Latency: 6267 ms
- Response Words: 53
- Similarity Score: 49.04/100
- Pass/Fail: Pass

---
### Q00002: Is there a minimum percentage or grade requirement in 10+2 (or equivalent) to be eligible to apply?
**Chatbot Answer**:
> To be eligible for admission into the B.Tech programs at Dhirubhai Ambani University, a candidate must have passed the final examination of 10+2 (Class XII) or its equivalent with Mathematics, Physics, and any one of Chemistry/Biotechnology/Computer Science/Biology. The minimum percentage of marks required is as prescribed by the All India Council for Technical Education (AICTE) from time to time. 
> 
> Candidates appearing in the qualifying examination in 2026 are also eligible to apply for provisional admission, provided they produce proof of having passed the qualifying examination by 30 October 2026.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Yes — per the 2026-27 eligibility table, most B.Tech programs (ICT, CS&AI, ECE-AI, EVD) require a minimum 60% aggregate in 10+2, while MnC and the new BS-MS programs require a minimum 65% aggregate.

**Meta Data**:
- Category: eligibility_criteria
- Latency: 8093 ms
- Response Words: 91
- Similarity Score: 38.69/100
- Pass/Fail: Fail

---
### Q00003: Which national-level entrance exams (like JEE Main, GATE, CAT) are accepted for admission?
**Chatbot Answer**:
> For undergraduate admissions at Dhirubhai Ambani University (DAU), the **Joint Entrance Examination (JEE) Main 2026** is the accepted national-level entrance exam for admission to B.Tech programs. Only candidates who have appeared for JEE (Main) 2026 are eligible to apply.
> 
> ### Application Process
> - There is a **single online application form** for all B.Tech programs, including B.Tech. (ICT), B.Tech (Honours) in ICT with minor in CS, B.Tech. (MnC), B.Tech. (EVD), B.Tech. (CS and AI), and B.Tech. (ECE-AI).
> - Applicants must select their program preferences in order of choice.
> - The **application fee** is **Rs. 1500/- plus 18% GST (Total: Rs. 1770/-)**, and it is non-refundable.
> - Candidates must meet the eligibility criteria to be considered for final admission.
> - Admission is based on the **All India Rank of JEE (Main) 2026**, and shortlisted candidates will be offered admission (confirmed/waitlisted) in order of merit.
> - Counselling is conducted online, and candidates are advised to check their email regularly for updates on their admission status.
> - Confirmed candidates must appear for **registration, document verification, and fee payment**.
> 
> If you need further details about postgraduate or doctoral admissions, please clarify, as the current documents only cover undergraduate admissions.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> B.Tech (All-India category) admission is based on JEE Main 2026 rank; the Gujarat category uses GUJCET (via ACPC). Ph.D. admission uses DAU's own entrance test (or an interview waiver in some cases) rather than JEE/GATE/CAT. GATE/CAT requirements for specific M.Tech/MBA-type programs are not detailed in this document.

**Meta Data**:
- Category: eligibility_criteria
- Latency: 12249 ms
- Response Words: 196
- Similarity Score: 35.97/100
- Pass/Fail: Fail

---
### Q00004: Are there any specific mandatory subjects (e.g., Physics, Chemistry, Mathematics) required in the 12th-grade curriculum?
**Chatbot Answer**:
> For admission into the B.Tech (MnC) program at DAU, there are no specific mandatory subjects explicitly mentioned in the retrieved documents for the 12th-grade curriculum. However, given the program's focus on computational and interdisciplinary domains, it is reasonable to infer that a strong background in subjects like Physics, Chemistry, and Mathematics would be beneficial. This is a common prerequisite for similar technical programs, though the documents do not confirm this directly. 
> 
> If you are seeking specific subject requirements, I recommend reaching out to the admissions office at DAU for the most accurate and updated information. You can visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in) for further assistance.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Yes — candidates must have passed 10+2 with Mathematics, Physics, and one of Chemistry/Bio-technology/Computer Science/Biology (MnC and the BS-MS programs specifically require Chemistry, not Biology or Computer Science).

**Meta Data**:
- Category: eligibility_criteria
- Latency: 8829 ms
- Response Words: 108
- Similarity Score: 36.66/100
- Pass/Fail: Fail

---
### Q00005: How does the eligibility and admission process differ for NRI, PIO, or foreign national students?
**Chatbot Answer**:
> For NRI (Non-Resident Indian), PIO (Person of Indian Origin), and foreign national students, the eligibility and admission process at Dhirubhai Ambani University (DAU) differ from the general admission process. Here's a detailed breakdown of the differences in eligibility, application process, and fee structure:
> 
> ### **Eligibility Criteria**
> 1. **NRI Students**:
>  - Overseas Citizen of India (OCI) cardholders.
>  - Individuals with a certificate of NRI status issued by the Indian Embassy or Consulate.
>  - Students who have studied outside India and have passed or are appearing for 10th or 12th standard (or equivalent) from an international education system.
>  - Students whose parents are NRI and can provide documentary proof of their status (e.g., a letter from the Indian Embassy/Consulate) valid until 31st August of the year of admission.
> 
> 2. **Foreign National Students**:
>  - Individuals who are citizens of a foreign country and do not hold NRI status.
> 
> 3. **PIO**:
>  - While the term "PIO" is not explicitly used in the retrieved documents, the eligibility for foreign nationals includes individuals of Indian origin who are citizens of other countries.
> 
> ### **Admission Process**
> - Admissions for NRI and foreign national students are conducted through the **Direct Admission of Foreign and NRI Students (DAFS)** category.
> - A total of **15% of the intake** in undergraduate (UG) programs is reserved for NRI and foreign national students.
> - The admission process is managed by the **International Student Cell (ISC)**, which coordinates the entire process based on predefined eligibility criteria.
> - The specific admission criteria for NRI and foreign national students can be found on the university's website: [Undergraduate Admissions - NRI and Foreign National (DAFS) Category](https://www.daiict.ac.in/undergraduate-admissions-nri-and-foreign-national-category).
> 
> ### **Fee Structure**
> - The fee structure for NRI and foreign national students is not explicitly detailed in the retrieved documents. However, the university provides a course-wise fee structure, which includes various components such as building fees, development fees, and other charges.
> - For detailed information on the fee structure, you can refer to the university's official fee structure documentation or contact the International Student Cell for specific details.
> 
> ### **Application Process**
> - The application process for NRI and foreign national students is streamlined through the DAFS category.
> - Applicants must submit the required documents, including proof of NRI status (if applicable), academic transcripts, and other relevant information as per the eligibility criteria.
> - The International Student Cell (ISC) handles the entire admission process for these students.
> 
> If you need further assistance or specific details about the application process, fee structure, or eligibility, you can contact the **International Student Cell** at Dhirubhai Ambani University for guidance.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> NRI/Foreign National (DAFS) candidates apply through a separate category with its own seat matrix (79 seats), timeline, and eligibility definitions (OCI cardholders, Indian-embassy-certified NRI status, or a parent residing abroad), and pay fees in USD rather than INR. PIO is not used as a distinct category in this document — NRI/OCI and Foreign National (FN) are the terms used.

**Meta Data**:
- Category: eligibility_criteria
- Latency: 19960 ms
- Response Words: 428
- Similarity Score: 41.46/100
- Pass/Fail: Fail

---
### Q00006: Is there any state quota, category reservation (SC/ST/OBC), or management quota applicable during admissions?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, here is the detailed response to your question:
> 
> 1. **State Quota or Category Reservation (SC/ST/OBC):** The documents retrieved do not mention any specific state quota or category reservation (such as SC/ST/OBC) for admissions in the M.Des., M.Sc. (IT), or Ph.D. programs at DAU. The eligibility and admission processes for these programs appear to be based on merit and general criteria without explicit mention of reservations.
> 
> 2. **Management Quota:** 
>  - For the **M.Des. program**, it is explicitly stated that there is no management quota. Admission is completely based on merit.
>  - For the **M.Sc. (IT) and Ph.D. programs**, the documents do not mention a management quota. The admission criteria for these programs are based on academic qualifications and merit.
> 
> 3. **Application Process and Fees Structure:**
>  - **M.Sc. (IT) Program:**
>  - **Eligibility:** A Bachelor’s degree from a recognized university in any stream with an aggregate of 60% marks, or its equivalent, is required. Candidates appearing in their final degree examination and expecting to complete it by July 2026 may also apply.
>  - **Fees Structure:** At the time of counseling, an amount of Rs. 1,75,000/- is required, which includes Rs. 1,50,000/- for tuition fee for the first semester and Rs. 25,000/- as a caution deposit. Additional fees include a registration fee of Rs. 2,500 per semester, hostel rent of Rs. 37,800 per semester, and food expenses of approximately Rs. 5,500 per month.
>  - **Ph.D. Program:**
>  - **Eligibility:** There is no age limit for this program.
>  - **Fees Structure:** At the time of admission, an amount of Rs. 50,000/- is required, which includes Rs. 25,000/- for tuition fee for the first semester and Rs. 25,000/- as a caution deposit. Additional fees include a registration fee of Rs. 2,500 per semester, hostel rent of Rs. 37,800 per semester, and food expenses of approximately Rs. 5,500 per month.
> 
> 4. **Requirements:** 
>  - For the **M.Sc. (IT) program**, candidates must submit their degree certificates or proof of completion of their degree by 30th October 2026. Failure to do so may result in the cancellation of their admission.
>  - For the **Ph.D. program**, the refund policy for withdrawing candidates is in accordance with UGC rules.
> 
> If you need further assistance or have additional questions, you can visit the official DAU website at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> All-India category SC/ST candidates are admitted on relaxed criteria compared to general-category candidates. Gujarat-category seats are administered by ACPC (the state counselling body) rather than DAU directly. No 'management quota' is mentioned in the available documents.

**Meta Data**:
- Category: eligibility_criteria
- Latency: 19495 ms
- Response Words: 387
- Similarity Score: 38.21/100
- Pass/Fail: Fail

---
### Q00007: What is the step-by-step process to fill out and submit the online application form?
**Chatbot Answer**:
> The step-by-step process to fill out and submit the online application form for document requests at DA-IICT is as follows:
> 
> 1. **Fill up the Online Application Form**: Access the online portal for document requests and fill out the required application form for the specific document(s) you need. 
>  - **Provide Necessary Information**: Supply your full name, student ID, program of study, registration number, and the specific documents you are requesting. 
>  - **Pay Applicable Charges**: After completing the form, you will be directed to a payment gateway where you can pay the applicable fees. 
>  - **Submit the Application**: Once the form is completed and fees are paid, your application will be automatically submitted to the Registrar’s Office for processing. 
> 
> 2. **Processing**: The institute verifies your eligibility and processes the request. If there are any queries, you will be contacted via your registered email ID or mobile number. The document is typically ready for pickup in two working days. 
> 
> 3. **Receive the Documents**: You will be notified when your documents are ready for pickup or delivery. If you opt for courier or postal delivery, the time to receive the documents will depend on the courier or postal service. 
> 
> For further assistance, you can contact the Alumni Document Service at **documents[at]dau[dot]ac[dot]in** or call **079-68261 574**.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The 2026-27 guide lists 6 steps: (1) apply online via the DAU-PWA admissions portal, (2) a merit list is published based on JEE Main/GUJCET scores, (3) shortlisted candidates attend counselling, (4) pay the initial tuition fee to confirm the seat, (5) original documents are verified on campus, (6) final enrollment/registration for first-semester courses.

**Meta Data**:
- Category: admission_process
- Latency: 10961 ms
- Response Words: 213
- Similarity Score: 36.01/100
- Pass/Fail: Fail

---
### Q00008: When does the online application portal usually open, and what is the last date to apply?
**Chatbot Answer**:
> The online application portal for the M.Sc. (Agriculture Analytics) and M.Sc. (IT) programs at Dhirubhai Ambani University (DAU) typically opens on **24 March 2026**. The last date to submit the online application is **05 June 2026**. 
> 
> Regarding the application process, fees structure, and requirements, the documents retrieved do not provide specific details on the fees or the exact requirements for application. However, they do mention that an entrance test is scheduled for **26 June 2026** for both programs. 
> 
> For more detailed information on fees and requirements, you may need to visit the official DAU website or contact the admissions office directly. You can find more information at [DAU Admissions](https://www.daiict.ac.in).
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> For the 2026-27 All-India category cycle, online applications opened 24 March 2026 and closed 1 June 2026 (the NRI/FN category's revised deadline for Round 1 was 3 June 2026).

**Meta Data**:
- Category: admission_process
- Latency: 8832 ms
- Response Words: 112
- Similarity Score: 34.44/100
- Pass/Fail: Fail

---
### Q00009: How much is the application processing fee, and is it refundable under any circumstances?
**Chatbot Answer**:
> The application processing fee and its refundability depend on the specific program you're applying to:
> 
> 1. **For Postgraduate Programs (e.g., M.Tech, M.Des.):** 
>  The application fee is **Rs. 1,770/-** (Rs. 1,500/- plus 18% GST) and is **non-refundable** under any circumstances.
> 
> 2. **For Ph.D. Programs:** 
>  The document retrieved does not mention an application fee specifically. Instead, it outlines a **Rs. 50,000/-** amount at the time of admission (Rs. 25,000/- for tuition and Rs. 25,000/- caution deposit). The caution deposit is **refundable at the end of the program**. However, no details about an application fee or its refundability are provided for Ph.D. admissions in the retrieved documents.
> 
> If you're applying to a program not mentioned here, please clarify, and I will check for further details.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> The B.Tech All-India application fee is Rs. 1,500 + 18% GST (Rs. 1,770 total); the NRI/FN (DAFS) fee is USD $150. Both are explicitly non-refundable — applications cannot be withdrawn for a refund.

**Meta Data**:
- Category: fees_and_payment
- Latency: 9671 ms
- Response Words: 125
- Similarity Score: 38.96/100
- Pass/Fail: Fail

---
### Q00010: What specific documents (certificates, mark sheets, ID proofs) must be uploaded during the application process?
**Chatbot Answer**:
> For the application process at Dhirubhai Ambani University (DAU), the specific documents that must be uploaded include:
> 
> 1. **Transcript**: A comprehensive record of the student’s academic performance throughout their tenure at DA-IICT, including grades for individual courses, cumulative CPI, and any relevant academic distinctions. This document is issued to the convocated or graduated student only.
> 
> 2. **CPI to Percentage Conversion Certificate**: A document that indicates the formula for converting CPI to percentage.
> 
> 3. **No Objection Certificate (NOC)**: An NOC document to join a program or course at another institute.
> 
> 4. **Other Documents**: Any additional documents as requested by the student for official or academic purposes.
> 
> The application process involves the following steps:
> 
> - **Fill up the Online Application Form**: Complete the required application form for the specific document(s) you need.
> - **Provide Necessary Information**: Supply required information such as your full name, student ID, program of study, registration number, and the specific documents you are requesting.
> - **Pay Applicable Charges**: After completing the form, you will be directed to a payment gateway where you can pay the applicable fees.
> - **Submit the Application**: Once the form is completed and the necessary fees are paid, your application will be automatically submitted to the Registrar’s Office for processing.
> - **Processing**: The document will typically be ready in two working days for in-person collection. If delivered via courier or post, the time depends on the courier or postal department.
> - **Receive the Documents**: You will be notified when your documents are ready for pickup or delivery.
> 
> For assistance, you can contact the Alumni Document Service at documents[at]dau[dot]ac[dot]in or call 079-68261 574.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Document verification (step 5 of the admissions procedure) covers 10th/12th mark sheets, the JEE scorecard, and category certificates; applicants missing their final JEE rank card can initially upload their admit card or last scorecard instead.

**Meta Data**:
- Category: admission_process
- Latency: 13173 ms
- Response Words: 270
- Similarity Score: 24.90/100
- Pass/Fail: Fail

---
### Q00011: How are the merit lists prepared, and where are they published?
**Chatbot Answer**:
> The merit lists for admissions are prepared based on the performance of candidates in qualifying exams or entrance tests. For GATE-qualified candidates, the merit list is prepared using their valid GATE scores, while for non-GATE candidates, it is based on their entrance test scores. 
> 
> The merit lists are published on the university's official website, and candidates are advised to regularly check the site for updates on their specialization allotments and the next steps in the counseling process. 
> 
> Regarding the application processing fee, it is non-refundable and amounts to Rs. 1500/- plus GST@ 18%, making the total Rs. 1770/-.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> For UG All-India admissions, the merit list is based on JEE Main scores (GUJCET/ACPC rank for the Gujarat category) and published as part of the admissions procedure; the exact publication channel (portal) is not detailed beyond 'the admissions procedure.' For Ph.D., the merit list is based on entrance-test and/or interview performance.

**Meta Data**:
- Category: admission_process
- Latency: 7841 ms
- Response Words: 100
- Similarity Score: 49.66/100
- Pass/Fail: Pass

---
### Q00012: What happens during the counseling rounds or physical document verification stage?
**Chatbot Answer**:
> During the counseling rounds or physical document verification stage at Dhirubhai Ambani University (DAU), candidates are required to complete several formalities to confirm their admission. These include:
> 
> 1. **Submission of Required Documents**: Candidates must present original documents for verification. These typically include academic certificates (10th and 12th standard or equivalent), age proof (date of birth as recorded in the 10th or 12th standard certificate), and other relevant documents. The decision of the concerned authorities of DAU regarding eligibility of any candidate shall be final.
> 
> 2. **Payment of Fees**: At the time of counseling, candidates must pay a specified amount. For example, for the M.Sc. (IT) program, the amount is Rs. 1,75,000/-, which includes Rs. 1,50,000/- towards tuition fee for the first semester and Rs. 25,000/- as a caution deposit. Additional fees such as registration fees and hostel rent are payable at the time of registration and allotment of hostel rooms.
> 
> 3. **Hostel and Accommodation Formalities**: Hostel rent is paid upon the allotment of a hostel room. For domestic students, the hostel rent is Rs. 37,800 per semester, while for international or NRI students, the fees are in USD and include off-campus hostel arrangements.
> 
> 4. **Education Loan Facilitation**: The Institute facilitates students to avail educational loans from selected banks. Bank officials are often present on campus during registration to assist students with loan procedures and documentation.
> 
> 5. **Refundable Caution Deposit**: The caution deposit is refundable at the end of the program, provided all conditions are met.
> 
> These steps ensure that candidates are formally admitted and prepared for the academic session.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Shortlisted candidates attend online/offline counselling; upon seat allocation they pay the initial tuition fee to confirm the seat, and then original documents (10th/12th mark sheets, JEE scorecard, category certificates) are verified on campus before final enrollment.

**Meta Data**:
- Category: admission_process
- Latency: 13540 ms
- Response Words: 262
- Similarity Score: 47.56/100
- Pass/Fail: Pass

---
### Q00013: Is there a personal interview or group discussion round required for postgraduate or doctoral admissions?
**Chatbot Answer**:
> For postgraduate or doctoral admissions at Dhirubhai Ambani University (DAU), the information provided in the retrieved documents does not explicitly mention the inclusion of a personal interview or group discussion round as part of the admission process. The details on the application process, admission criteria, fee structure, and financial assistance can be found on the university's admissions page.
> 
> If you are seeking more detailed information or have specific questions about the admission process for postgraduate or doctoral programs, it is recommended to visit the university's official website at https://www.daiict.ac.in for the most accurate and up-to-date information.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Ph.D. admission requires a personal interview at DAU (after an entrance test or a waiver), evaluated on foundational and specialized topics, supported by a one-page Statement of Purpose. No group discussion round is mentioned for Ph.D. or other PG programs in the available documents.

**Meta Data**:
- Category: admission_process
- Latency: 7666 ms
- Response Words: 98
- Similarity Score: 53.33/100
- Pass/Fail: Pass

---
### Q00014: How can I check my current admission status, rank, or waitlist movement?
**Chatbot Answer**:
> I'm having trouble reaching the student records system right now. Please try again in a moment.

**Actual Answer (Expected)**:
> Not covered in the available admissions documents; status/rank/waitlist tracking would be through the official DAU-PWA admissions portal, but no dedicated status-checking page was found in this corpus.

**Meta Data**:
- Category: admission_process
- Latency: 1037 ms
- Response Words: 16
- Similarity Score: 38.85/100
- Pass/Fail: Fail

---
### Q00015: What is the procedure for formally accepting the admission offer once I am selected?
**Chatbot Answer**:
> The procedure for formally accepting an admission offer at Dhirubhai Ambani University (DAU) involves several key steps, as outlined in the provided documentation:
> 
> 1. **Online Application and Fee Payment**: Candidates must submit an online application form and pay a non-refundable application fee of Rs. 1500/- plus GST@ 18% (Total Rs. 1770/-).
> 
> 2. **Eligibility and Merit Lists**: 
>  - For GATE-qualified candidates, the merit list is prepared based on their valid GATE scores. Counseling for specialization allotment is conducted online.
>  - For non-GATE qualified candidates, the merit list is prepared based on the entrance test scores. These candidates must appear for an entrance test conducted at selected centers.
> 
> 3. **Counseling and Specialization Allotment**: 
>  - Shortlisted candidates are offered admission (confirmed or waitlisted) based on their merit. Counseling is conducted online.
>  - Candidates are advised to regularly check the university website for updates on specialization allotment and the steps to continue with the counseling process.
> 
> 4. **Registration and Document Verification**: 
>  - Candidates who have accepted admission offers must appear for registration, document verification, and payment of fees.
> 
> 5. **Orientation**: 
>  - After registration and document verification, there will be an orientation for candidates who have been given confirmed admission.
> 
> 6. **Choice of Specializations**:
>  - Candidates can specify up to two choices of specialization. If admitted to their second choice, they remain on the waitlist for their first choice until the admission process is closed.
>  - Once the admission process is closed, changes to the specialization are not allowed at any point in the program.
> 
> For more detailed information, you can visit the university's official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Acceptance is effected by paying the initial tuition fee upon seat allocation (step 4 of the admissions procedure) to confirm the seat, followed by document verification and enrollment.

**Meta Data**:
- Category: admission_process
- Latency: 13621 ms
- Response Words: 265
- Similarity Score: 28.57/100
- Pass/Fail: Fail

---
### Q00016: What is the detailed fee structure (tuition, development, registration) for the first year of the program?
**Chatbot Answer**:
> The detailed fee structure for the first year of the program includes the following components:
> 
> 1. **Tuition Fee**: For the first semester, the tuition fee is **Rs. 1,50,000** for the M.Des. program. For the Ph.D. program, it is **Rs. 25,000** per semester.
> 
> 2. **Registration Fee**: A registration fee of **Rs. 2,500 per semester** is applicable for both the M.Des. and Ph.D. programs.
> 
> 3. **Caution Deposit**: A caution deposit of **Rs. 25,000** is required at the time of admission for both programs. This amount is refundable at the end of the program.
> 
> 4. **Hostel Rent**: If a hostel room is allotted, the hostel rent is **Rs. 37,800 per semester** for both programs.
> 
> 5. **Food Expenses**: Food expenses are on actuals and vary depending on the food options chosen. The approximate monthly expense is **Rs. 5,500**.
> 
> 6. **Fee Revisions**: The fees are subject to revision every academic year by **8 to 10%**.
> 
> For the M.Des. program, an additional amount of **Rs. 1,75,000** is to be paid at the time of admission, which includes **Rs. 1,50,000** for the tuition fee and **Rs. 25,000** as a caution deposit.
> 
> If you need further assistance or clarification, you can visit the official website at [DAU Admissions](https://www.daiict.ac.in).
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> For B.Tech (2025-26): Tuition Fee Rs. 1,92,500/semester, Registration Fee Rs. 2,500/semester, one-time refundable Caution Deposit Rs. 25,000 — totaling Rs. 2,17,500 due at admission for Semester 1 plus the deposit.

**Meta Data**:
- Category: fees_and_payment
- Latency: 13144 ms
- Response Words: 203
- Similarity Score: 58.91/100
- Pass/Fail: Pass

---
### Q00017: Are there different fee structures for different categories of students (e.g., All India Quota vs. State Quota)?
**Chatbot Answer**:
> Yes, the fee structure at Dhirubhai Ambani University (DAU) is subject to revision every academic year, with an expected increase of 8 to 10% annually. However, the documents retrieved do not explicitly mention whether there are different fee structures for different categories of students (e.g., All India Quota vs. State Quota). The fee structure is described as being submitted to the Appellate Committee of the State Government for consideration, and it is subject to revision every academic year. 
> 
> For specific programs like B.Tech. (EVD), there is an additional value-added course fee of Rs. 18,000 for the SHILP course, which is to be paid along with the second-semester tuition fee. 
> 
> If you need more detailed information about the fee structure for specific categories, I recommend visiting the official DAU website at [https://www.daiict.ac.in](https://www.daiict.ac.in) or contacting the admissions office directly for the most accurate and up-to-date information.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> All-India and Gujarat category B.Tech students pay the same domestic fee structure (~Rs. 1,92,500/semester tuition); NRI/DAFS category students instead pay a separate structure quoted in USD (~$6,000/semester tuition per the fee policy document; $4,000/semester per the 2026-27 comprehensive guide), so the exact NRI figure differs slightly between the two source documents.

**Meta Data**:
- Category: fees_and_payment
- Latency: 9835 ms
- Response Words: 148
- Similarity Score: 37.42/100
- Pass/Fail: Fail

---
### Q00018: Does the initial fee payment include hostel accommodation and mess charges, or are those paid separately?
**Chatbot Answer**:
> The initial fee payment at DAU does **not** include hostel accommodation and University Dining Services (Mess) charges. These are paid separately. 
> 
> - **Hostel Rent**: Rs. 37,800 per semester, payable upon allotment of the hostel room.
> - **Food Expenses**: On actuals, with an approximate monthly cost of Rs. 5,500. Multiple food options are available on campus.
> 
> The initial payment includes tuition, registration, and a caution deposit. Specifically:
> - **Tuition Fee**: Rs. 1,50,000 per semester.
> - **Registration Fee**: Rs. 2,500 per semester.
> - **Caution Deposit**: Rs. 25,000 (refundable at the end of the program).
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No — hostel rent (Rs. 37,800/semester) and food/mess charges (on actuals, approx. Rs. 5,500/month) are listed as separate line items from the tuition/registration/caution-deposit fee due at admission.

**Meta Data**:
- Category: fees_and_payment
- Latency: 8817 ms
- Response Words: 95
- Similarity Score: 41.18/100
- Pass/Fail: Fail

---
### Q00019: What is the strict deadline for paying the first-semester fees to confirm and secure my seat?
**Chatbot Answer**:
> To confirm and secure your seat at Dhirubhai Ambani University (DAU), you must strictly adhere to the deadline for paying the first-semester fees. According to the admissions guidelines for the M.Des. and M.Sc. (IT) programs, candidates must submit their degree certificates or proof of completion of their degree **before 30 October 2026**. Failure to meet this deadline may result in the cancellation of your admission. 
> 
> Additionally, at the time of admission, you are required to pay an amount of **Rs. 1,75,000/-**, which includes **Rs. 1,50,000/- for the tuition fee for the first semester** and **Rs. 25,000/- as a caution deposit**. The registration fee and hostel rent are payable separately at the time of registration and upon allotment of a hostel room, respectively. 
> 
> If you require assistance with an educational loan, the Institute facilitates students in availing loans from selected banks and will support you in completing the loan documentation process.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> The 'Fees Payment window for shortlisted candidates' is listed as TBD in the 2026-27 Important Dates table for the All-India category — the exact date had not been finalized as of the source document's scrape date.

**Meta Data**:
- Category: fees_and_payment
- Latency: 10036 ms
- Response Words: 153
- Similarity Score: 31.65/100
- Pass/Fail: Fail

---
### Q00020: What is the exact fee refund policy if I decide to withdraw my admission before or after the academic session begins?
**Chatbot Answer**:
> DAU follows a structured fee refund policy for students who decide to withdraw from their admission, based on UGC guidelines. The refund percentages depend on the timing of the withdrawal:
> 
> - **Before the commencement of classes**: A full refund is provided, deducting only the processing fee.
> - **Within 15 days after the commencement of classes**: 80% of the tuition fee is refunded.
> - **Between 16–30 days after the commencement of classes**: 50% of the tuition fee is refunded.
> - **Between 31–90 days after the commencement of classes**: 25% of the tuition fee is refunded.
> - **After 90 days**: No refund is provided.
> 
> Additionally, students may drop courses within the **add/drop period** (first 2 weeks of the semester) without academic penalty, and fee adjustments for dropped courses are processed by the Finance Office.
> 
> For specific programs such as the **BS–MS in Data Science & Artificial Intelligence** and **BS–MS in Information Technology**, the refund policy is also in accordance with UGC rules. 
> 
> If you have further questions or need assistance, you can reach out to the university's Finance Office or visit the [DAU admissions page](https://www.daiict.ac.in/admissions) for more details.
> 
> [Sources: 1, 3, 4, 5]

**Actual Answer (Expected)**:
> Per UGC guidelines followed by DAU: full refund (minus processing fee) before classes commence; 80% refund within 15 days of commencement; 50% refund 16-30 days after; 25% refund 31-90 days after; no refund after 90 days. The Rs. 25,000 caution deposit remains refundable at program end regardless, subject to no-dues clearance.

**Meta Data**:
- Category: fees_and_payment
- Latency: 11518 ms
- Response Words: 191
- Similarity Score: 43.21/100
- Pass/Fail: Fail

---
### Q00021: Are there any merit-based or means-based scholarships or financial aid programs available for newly admitted students?
**Chatbot Answer**:
> Yes, Dhirubhai Ambani University (DAU) offers merit-based and means-based scholarships or financial aid programs for newly admitted students. These include both institute-level and external scholarships. Here are the details:
> 
> 1. **Merit Scholarship** 
>  - **Eligibility**: Top SPI (Semester Performance Index) performers each semester. 
>  - **Benefit**: Full or partial tuition fee reimbursement.
> 
> 2. **BS+MS Institute Fellowship** 
>  - **Eligibility**: Students with a national-level entrance rank or board merit. 
>  - **Benefit**: 100% tuition fee coverage.
> 
> 3. **DAFS Merit Scholarship** 
>  - **Eligibility**: Merit-based support for NRI (Non-Resident Indian) or foreign national category students. 
>  - **Benefit**: Merit-based fee support.
> 
> 4. **Cybage Khushboo Scholarship** 
>  - **Eligibility**: For students in the ICT (Information and Communication Technology) or law domain with a family income of less than ₹5 lakh. 
>  - **Benefit**: Up to 80% tuition fee coverage or ₹1,50,000 per annum, whichever is lower.
> 
> Additionally, the university provides **scholarships and financial assistance** to eligible students based on academic merit and other criteria for programs like BS–MS in Information Technology and Data Science & Artificial Intelligence.
> 
> For more detailed information, you can visit the **Fee & Scholarships** page on the university's official website.
> 
> [Sources: 1, 2, 3, 4, 5]

**Actual Answer (Expected)**:
> Yes — DAU lists multiple scholarship programs including B.Tech DAFS Merit Scholarships, B.Tech Institute Fellowships/Scholarships, HEST Scholarships, Gujarat Government financial assistance, and program-specific scholarships for M.Sc. Data Science, M.Sc. Agriculture Analytics, BS-MS, and others.

**Meta Data**:
- Category: fees_and_payment
- Latency: 12468 ms
- Response Words: 189
- Similarity Score: 36.92/100
- Pass/Fail: Fail

---
### Q00022: Is there a provision for paying the semester fees in installments or via a student loan?
**Chatbot Answer**:
> Yes, Dhirubhai Ambani University (DAU) provides provisions for students to pay their semester fees through **education loans**. The university facilitates students in availing educational loans from selected banks. During the registration process, bank officials will be present on campus to assist students with the procedures and terms and conditions of the loan. Additionally, students can also opt for loans from banks of their choice, and the university will support them in completing the loan documentation process.
> 
> However, the documents retrieved do not mention a specific **installment-based payment system** for the fees. The fee structure for the first semester includes a lump-sum payment of tuition, caution deposit, and other charges at the time of admission or counseling. If you are considering an installment-based payment system, you may need to contact the university's admissions or finance office for further clarification.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> No installment plan is documented; educational loans are supported — students can avail loans from banks of their choice, and the Institute assists with the loan-documentation process.

**Meta Data**:
- Category: fees_and_payment
- Latency: 9261 ms
- Response Words: 142
- Similarity Score: 65.12/100
- Pass/Fail: Pass

---
### Q00023: What are the accepted modes of payment for the admission and tuition fees (e.g., Net Banking, UPI, Demand Draft)?
**Chatbot Answer**:
> The accepted modes of payment for admission and tuition fees at Dhirubhai Ambani University (DAU) are not explicitly listed in the retrieved documents. However, the university facilitates students in availing educational loans from selected banks, and bank officials are present on campus during registration to assist with loan procedures and documentation. 
> 
> For specific modes of payment such as Net Banking, UPI, or Demand Draft, this information is not available in the current documents. You may contact the university's admissions office or visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in) for further clarification.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Not explicitly listed in the available documents; the Ph.D. admissions page notes only that the 'mode of payment will be informed' separately, so specific accepted payment channels are not documented here.

**Meta Data**:
- Category: fees_and_payment
- Latency: 7864 ms
- Response Words: 92
- Similarity Score: 61.42/100
- Pass/Fail: Pass

---
### Q00024: Are there any hidden charges or one-time refundable caution deposits required at the time of admission?
**Chatbot Answer**:
> Yes, there are one-time refundable caution deposits required at the time of admission for both domestic and international/NRI students. For domestic students, the caution deposit is **Rs. 25,000**, and for international/NRI students, it is **US $1,000**. These amounts are refundable at the end of the program. 
> 
> Additionally, there are no mentions of hidden charges in the provided documents. The fee structure explicitly outlines the tuition, registration, caution deposit, and hostel-related charges.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> There are no 'hidden' charges described — a one-time Rs. 25,000 Caution Deposit is charged at admission and is explicitly refundable at the end of the program, subject to no outstanding dues or property damage.

**Meta Data**:
- Category: fees_and_payment
- Latency: 7625 ms
- Response Words: 74
- Similarity Score: 66.44/100
- Pass/Fail: Pass

---
### Q00025: How can I contact the admissions office if I face technical issues with the payment gateway or the application portal?
**Chatbot Answer**:
> If you face technical issues with the payment gateway or the application portal, you can contact the admissions office for assistance. According to the university's resources, detailed information about the application process, admission criteria, fee structure, and support for technical issues can be found on the official admissions page. You can visit the [Admissions page](https://www.daiict.ac.in/admissions#tab-1) for further assistance. 
> 
> For direct contact, you may also reach out to the university's general contact information available on their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> Fee-related queries: ug_admissions@dau.ac.in; NRI/Foreign-category helpline: (+91) 8488876445. The 2026-27 guide additionally lists role-specific contacts, e.g. Dean of Admissions for grievance redressal.

**Meta Data**:
- Category: admission_process
- Latency: 7808 ms
- Response Words: 81
- Similarity Score: 33.93/100
- Pass/Fail: Fail

---
### Q00026: What is the percentage weightage of the Mid-Semester examination in the final overall grade of a course?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> There is no fixed institute-wide percentage — the distribution of weightage across continuous-evaluation components (including the mid-semester exam) and the end-semester exam is set by each course instructor and announced at the start of the semester.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3692 ms
- Response Words: 30
- Similarity Score: 42.08/100
- Pass/Fail: Fail

---
### Q00027: How long is the standard duration of a typical Mid-Semester written exam?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> The Examination Rules describe a typical in-semester (mid-semester) exam duration of 1 hour, versus a typical 3-hour duration for end-semester exams.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3525 ms
- Response Words: 30
- Similarity Score: 38.96/100
- Pass/Fail: Fail

---
### Q00028: Are regular classes or lab sessions held during the Mid-Semester examination week?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Not explicitly stated, but the Academic Calendar lists dedicated In-Semester Examination windows (e.g. 31 Aug-5 Sep 2026) as separate blocks from the regular teaching period, implying the exam week is set apart from normal class scheduling.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3933 ms
- Response Words: 30
- Similarity Score: 42.96/100
- Pass/Fail: Fail

---
### Q00029: What is the procedure if a student misses a Mid-Semester exam due to severe medical reasons or family emergencies?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> The academic requirements document specifies an 'I' (Incomplete) grade process for a missed end-semester exam with Dean (AP) approval and medical/other documentation, but a mid-semester-specific missed-exam procedure is not separately detailed in the available documents — students would need to consult the Medical Facilities & Emergency Procedure document and the Dean (AP) office.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3761 ms
- Response Words: 30
- Similarity Score: 41.25/100
- Pass/Fail: Fail

---
### Q00030: What is the exact weightage of the End-Semester examination compared to continuous evaluation (quizzes, assignments)?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Not fixed institute-wide — like the mid-sem weightage, the split between the end-semester exam and continuous-evaluation components (assignments, quizzes, labs, viva-voce, etc.) is decided by the individual course instructor at the start of the semester.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3793 ms
- Response Words: 30
- Similarity Score: 40.29/100
- Pass/Fail: Fail

---
### Q00031: How is the syllabus divided? Does the End-Semester exam cover the entire course syllabus or just the post-midsem topics?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Not explicitly stated in the available academic requirements documents; syllabus coverage for the end-semester exam is set by individual course instructors and would appear in each course's specific course policy document.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3738 ms
- Response Words: 30
- Similarity Score: 46.11/100
- Pass/Fail: Pass

---
### Q00032: What is the typical format of the End-Semester exams (e.g., subjective, objective, open-book, take-home)?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Assessment modes listed institute-wide include tests that may be open or closed book, along with assignments, quizzes, and viva-voce; the specific end-semester format for a given course is set by that course's instructor.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3669 ms
- Response Words: 30
- Similarity Score: 40.61/100
- Pass/Fail: Fail

---
### Q00033: How are practical exams, lab evaluations, and project vivas conducted at the end of the semester?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Viva-voce and laboratory work are listed among the standard continuous-evaluation modes, but a detailed institute-wide procedure specifically for end-of-semester practical exams/lab evaluations is not laid out beyond this — it is governed at the course level.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3691 ms
- Response Words: 30
- Similarity Score: 43.72/100
- Pass/Fail: Fail

---
### Q00034: What is the university's strict disciplinary policy regarding cheating or academic malpractice during examinations?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Malpractice is adjudicated clause-by-clause by the examinations authority: possessing unauthorized material or communicating with others leads to expulsion from the exam hall and cancellation of that exam's performance (with no supplementary exam); mass cheating or impersonation can lead to a fail grade and referral to the Disciplinary Action Committee; repeat offenders are debarred from subsequent exams that semester.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3647 ms
- Response Words: 30
- Similarity Score: 39.72/100
- Pass/Fail: Fail

---
### Q00035: Can a student request a re-evaluation, recounting, or viewing of their End-Semester exam answer scripts if they are unsatisfied with their marks?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Yes, in effect — the Grading Policy describes a Grade Appeal Process: a student who believes there is an error in their grade can appeal through the Controller of Examinations (CoE) within the academic-calendar timeline, and the appeal is reviewed by the Course Instructor and Dean (Academic Programs). A separate answer-script 'recounting/viewing' procedure is not spelled out beyond this.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3769 ms
- Response Words: 30
- Similarity Score: 43.88/100
- Pass/Fail: Fail

---
### Q00036: What is the grading system used by the university (e.g., relative grading on a curve vs. absolute grading)?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> DAU uses a 10-point letter grading system (AA=10 down to F=0). The available documents do not explicitly state whether grades are curved (relative) or absolute within a course — that detail is not specified.

**Meta Data**:
- Category: grading_system
- Latency: 3688 ms
- Response Words: 30
- Similarity Score: 40.63/100
- Pass/Fail: Fail

---
### Q00037: What are the different letter grades awarded (e.g., AA, AB, BB), and what are their corresponding numerical grade points?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> AA=10 (Outstanding), AB=9, BB=8, BC=7, CC=6, CD=5, DD=4 (Pass, Marginal), DE=3 (Poor), F=0 (Fail), plus non-numeric grades I (Incomplete), W (Withdrawn), and P (Pass, audit courses, excluded from CPI).

**Meta Data**:
- Category: grading_system
- Latency: 3663 ms
- Response Words: 30
- Similarity Score: 32.80/100
- Pass/Fail: Fail

---
### Q00038: What is the minimum letter grade required to successfully pass a course?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> DE (3 grade points) is the minimum passing grade for a regular course; F (0) is a fail. Pass/Fail-designated courses instead use a P or F grade.

**Meta Data**:
- Category: grading_system
- Latency: 3579 ms
- Response Words: 30
- Similarity Score: 39.09/100
- Pass/Fail: Fail

---
### Q00039: What does an 'I' (Incomplete) or 'X' grade mean on a transcript, and what is the process to resolve it?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> 'I' (Incomplete) is awarded when a student's performance is otherwise satisfactory but they miss the end-semester exam for an approved medical/exceptional reason; it must be converted to a performance grade (via an equivalent exam) by the specified next-semester deadline, or it converts to 'F'. An 'X' grade is not part of the standard B.Tech grading scale — it appears only in Ph.D. program documents as an 'unsatisfactory' research-progress grade, where accumulating more than one X in a semester (or CPI below 7/10) triggers review.

**Meta Data**:
- Category: grading_system
- Latency: 3980 ms
- Response Words: 30
- Similarity Score: 34.70/100
- Pass/Fail: Fail

---
### Q00040: What is the mathematical formula used to calculate the Semester Grade Point Average (SGPA)?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> DAU calls this the Semester Performance Index (SPI): SPI = Σ(Ci × Gi) / ΣCi, the credit-weighted average of grade points across all courses registered in that semester.

**Meta Data**:
- Category: grading_system
- Latency: 3645 ms
- Response Words: 30
- Similarity Score: 42.69/100
- Pass/Fail: Fail

---
### Q00041: How is the Cumulative Performance Index (CPI) or Cumulative Grade Point Average (CGPA) calculated across multiple semesters?
**Chatbot Answer**:
> The **Cumulative Performance Index (CPI)**, also known as the **Cumulative Grade Point Average (CGPA)**, is calculated as a weighted average of the grade points obtained across all semesters. The formula for CPI is:
> 
> $$
> \text{CPI} = \frac{\sum_{\text{all semesters}} (C_i \times G_i)}{\sum_{\text{all semesters}} C_i}
> $$
> 
> Where:
> - $C_i$ is the credit of the $i$-th course.
> - $G_i$ is the grade points obtained in that course.
> 
> This calculation aggregates the performance of a student across all semesters, factoring in both the credit hours and the grade points earned in each course.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> CPI = Σ(Ci × Gi) / ΣCi, summed across all semesters — the credit-weighted average of grade points obtained over the student's entire academic record.

**Meta Data**:
- Category: grading_system
- Latency: 9264 ms
- Response Words: 91
- Similarity Score: 53.54/100
- Pass/Fail: Pass

---
### Q00042: Do failed courses (F grades) negatively affect the CPI, and how are they accounted for when the student eventually clears the course?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> An F grade (0 points) pulls CPI down and must be cleared by repeating the course as a backlog. For DD/DE grade-improvement repeats, the new grade replaces the old one in the CPI calculation while the original attempt still shows on the transcript; degree completion also requires clearing all F grades entirely (no outstanding F).

**Meta Data**:
- Category: grading_system
- Latency: 3683 ms
- Response Words: 30
- Similarity Score: 42.02/100
- Pass/Fail: Fail

---
### Q00043: What is the absolute minimum CPI required to graduate and receive the degree?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> A minimum final CPI of 5.0 (with at least 760 total grade points and completion of at least 175 credits, and no outstanding F grades) is required to graduate with the standard B.Tech degree.

**Meta Data**:
- Category: grading_system
- Latency: 3578 ms
- Response Words: 30
- Similarity Score: 42.05/100
- Pass/Fail: Fail

---
### Q00044: Is there a minimum CPI cutoff requirement to be eligible to sit for campus placements or internships?
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), there is a minimum CPI requirement for specific academic milestones, such as the Ph.D. program. For example, Ph.D. students must maintain a minimum CPI of 7.0 for graduation. However, the documents retrieved do not explicitly mention a minimum CPI cutoff requirement for eligibility to sit for campus placements or internships. 
> 
> For internships, such as the Summer Research Internship, eligibility is determined by individual faculty mentors, and specific criteria like minimum CPI, coursework, or prerequisites are decided on a case-by-case basis. 
> 
> If you are looking for a specific CPI requirement for campus placements or internships, it would be best to consult the respective placement or internship coordinators at the university for the most accurate and updated information.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No fixed institute-wide CPI cutoff was found in the placement documents reviewed; individual companies set their own eligibility criteria (including any CPI cutoff) via the Job Announcement Form (JAF) they submit to the Placement Office as part of the standard recruitment pipeline.

**Meta Data**:
- Category: grading_system
- Latency: 8322 ms
- Response Words: 124
- Similarity Score: 45.37/100
- Pass/Fail: Pass

---
### Q00045: What is the official formula to convert the 10-point scale CPI/CGPA into an equivalent percentage for external applications?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Not documented in the available academic policy files — no official CPI-to-percentage conversion formula was found in this corpus.

**Meta Data**:
- Category: grading_system
- Latency: 3586 ms
- Response Words: 30
- Similarity Score: 45.25/100
- Pass/Fail: Pass

---
### Q00046: What happens if a student fails a core compulsory course? Do they need to repeat the entire semester's classes or just retake the exam?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> A student who fails a course (F grade) must repeat that specific course as a backlog course — not the entire semester's classes. However, if CPI falls below 4.0 at the end of the 2nd or 4th semester specifically, the student may be asked to repeat a full year (with course-improvement options) or be discontinued.

**Meta Data**:
- Category: grading_system
- Latency: 3804 ms
- Response Words: 30
- Similarity Score: 42.01/100
- Pass/Fail: Fail

---
### Q00047: Are there supplementary, remedial, or make-up exams available for students who fail the End-Semester exams?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> There isn't a separate 'supplementary exam' immediately after end-sem; instead, students register for backlog courses in the Summer Semester (an ~8-week window between May and July), where they can retake up to 3 backlog courses with F or DE grades.

**Meta Data**:
- Category: grading_system
- Latency: 3831 ms
- Response Words: 30
- Similarity Score: 42.82/100
- Pass/Fail: Fail

---
### Q00048: What are the specific rules regarding academic probation, semester drops, or termination if a student's CPI falls below a certain critical threshold?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> A student is placed on Academic Probation if 1st-semester SPI < 4.5, or in later semesters if CPI < 5.0 or the previous semester's SPI < 4.5. If CPI is below 4.0 at the end of the 2nd or 4th semester, the student must repeat a year or be discontinued. Degree completion is capped at 6 academic years maximum.

**Meta Data**:
- Category: grading_system
- Latency: 3787 ms
- Response Words: 30
- Similarity Score: 45.82/100
- Pass/Fail: Pass

---
### Q00049: How and when are the official semester grade cards and final degree transcripts issued to the students?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Semester-wise mark sheets and combined grade reports are issued through the Students Document Service portal on request; per the Academic Calendar, results for a semester (e.g. Autumn 2026-27) are announced around 14 December 2026, after which grade documents become available.

**Meta Data**:
- Category: grading_system
- Latency: 3666 ms
- Response Words: 30
- Similarity Score: 43.54/100
- Pass/Fail: Fail

---
### Q00050: Can a student opt to take extra elective courses to improve their overall CPI, and how does the grading system handle these extra credits?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Grade improvement is limited to repeating a course in which a DD or DE grade was already obtained (only if CPI < 5.0), in a regular semester; only one Backlog/Grade-Improvement course may be registered per regular semester. This is course-repetition for improvement, not simply adding arbitrary extra electives to raise CPI.

**Meta Data**:
- Category: grading_system
- Latency: 3728 ms
- Response Words: 30
- Similarity Score: 43.16/100
- Pass/Fail: Fail

---
### Q00051: List every official student club at DAU and categorize them into Technical, Cultural, Professional, Sports, Media and Hobby clubs.
**Chatbot Answer**:
> Based on the information retrieved from the university knowledge base, here is a categorized list of the official student clubs at Dhirubhai Ambani University (DAU):
> 
> ---
> 
> ### **Technical Clubs**
> 1. **Programming Club** 
>  - Focus: Coding, algorithm development, and participation in competitive programming events like ACM ICPC. 
>  - Contact: Vraj K. Dobariya (Convener), Devang S. Vaghani (Deputy Convener) 
>  - Email: programming-club@dau.ac.in 
> 
> 2. **Research Club** 
>  - Focus: Research papers, tech talks, and industry collaborations. 
>  - Convener: Gulafsha Bhatti 
>  - Email: research_club@dau.ac.in 
> 
> 3. **Electronics Hobby Club (EHC)** 
>  - Focus: Arduino, Raspberry Pi, NFC Door-Lock, RC Car, Drones. 
>  - Convener: Kaushik Prajapati 
>  - Email: ehc@dau.ac.in 
> 
> ---
> 
> ### **Cultural Clubs**
> 1. **Music Club** 
>  - Focus: Music creation, performances, and workshops. 
>  - Convener: Harsh Popatiya 
>  - Deputy Convener: Varnika Chhawcharia 
>  - Email: music_club@dau.ac.in 
> 
> 2. **DAU Theatres Group** 
>  - Focus: Performing arts in forms like Mono Act, Street Play, Stage Play, and Mime. 
>  - Convener: Rishank Dudhat 
>  - Deputy Convener: Gantavya Mayal 
>  - Email: theatres@dau.ac.in 
> 
> ---
> 
> ### **Hobby Clubs**
> 1. **Chess Club** 
>  - Focus: Chess learning, practice, and competition. 
>  - Convener: Aarya Shah 
>  - Email: chess_club@dau.ac.in 
> 
> 2. **Photography & Movie Making Club (PMMC)** 
>  - Focus: Workshops, photowalks, and training in photography and filmmaking. 
>  - Convener: Ayush Gandhi 
>  - Email: pmmc@dau.ac.in 
> 
> ---
> 
> ### **Sports, Professional, and Media Clubs**
> - The provided documents do not explicitly list clubs in these categories. If you are looking for specific clubs related to sports, professional development, or media, I recommend visiting the official DAU website or contacting the Dean (Students) office for more information.
> 
> ---
> 
> ### **Notes**
> - The total number of clubs mentioned in the documents is 22, but only a few are detailed in the retrieved context. For a complete list, you may need to refer to the full "Dean (Students) – Comprehensive Guide (v2)" document or reach out to the Dean (Students) office for updated information. 
> 
> Let me know if you'd like help finding contact details for any specific club!

**Actual Answer (Expected)**:
> The SBG Constitution lists 21 official clubs (AI Club, Business Club, Chess Club, Cubing Club, Cyber Information & Network Security Club, DA-IICT Theatres Group, Dance Club, The Debating Society, GDG On Campus, Electronics Hobby Club, Film Club, Headrush Quizzing Club, Khelaiya Club, Microsoft Student Technical Club, Muse Club, Music Club, Photography & Movie Making Club, Press Club, Programming Club, Radio Club, Research Club) plus 1 dormant club (Heritage Club). The source does not itself sort these into Technical/Cultural/Professional/Sports/Media/Hobby buckets — that categorization would need to be inferred from each club's stated purpose.

**Meta Data**:
- Category: club_committee_directory
- Latency: 18400 ms
- Response Words: 321
- Similarity Score: 41.80/100
- Pass/Fail: Fail

---
### Q00052: List every official committee at DAU and explain how committees differ from clubs.
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), **student committees** and **student clubs** serve distinct purposes and operate under different structures. Below is a list of the official student committees and an explanation of how they differ from clubs.
> 
> ---
> 
> ### **Official Student Committees at DAU (2026 Academic Year)**
> 
> 1. **Academic Committee** 
>  - Role: Interface between the student community and institute administration for academic development. 
>  - Convener: Zeel Ghori 
>  - Email: sbg_academics@dau.ac.in
> 
> 2. **Annual Festival Committee** 
>  - Role: Conducts Synapse (Annual Techno-Cultural Fest), HackOut (Hackathon), and YouthRun (Marathon). 
>  - Convener: Rishabh Jain 
>  - Email: synapse@dau.ac.in
> 
> 3. **Cafeteria Management Committee (CMC)** 
>  - Role: Addresses cafeteria issues, conducts inspections, and ensures hygiene. 
>  - Convener: Yug Tejani 
>  - Email: cmc@dau.ac.in
> 
> 4. **Cultural Committee** 
>  - Role: Organizes cultural expression events, festivals, and talent showcases. 
>  - Convener: Ansh Garg 
>  - Email: cultural@dau.ac.in
> 
> 5. **Hostel Management Committee (HMC)** 
>  - Role: Ensures a peaceful, clean, and student-friendly hostel environment. 
>  - Convener: Dweep Kotecha 
>  - Email: hmc@dau.ac.in
> 
> 6. **TechSupport Committee** 
>  - Role: Represents student ICT resource issues (Wi-Fi, Printers) and provides technical assistance for campus events. 
>  - Convener: Parshwa Modi 
>  - Email: tech_support@dau.ac.in
> 
> 7. **Sports Committee** 
>  - Role: Promotes fitness and teamwork; organizes Concours, DCL, Inter-Wing Tournament, and Freshers' Weekend. 
>  - Convener: Ishan Thakkar 
>  - Email: sports@dau.ac.in
> 
> 8. **Student Placement Cell (SPC)** 
>  - Role: Acts as a bridge between students and the placement office; organizes mock interviews and company sessions. 
>  - Convener: Rishit Unadkat 
>  - Email: spc@dau.ac.in
> 
> ---
> 
> ### **How Committees Differ from Clubs**
> 
> - **Committees** are administrative bodies formed to manage specific functional areas of student life. They are typically appointed or elected to address operational, logistical, or administrative needs of the campus. For example, the Cafeteria Management Committee ensures hygiene and quality in the cafeteria, while the Hostel Management Committee maintains the hostel environment. These committees are usually more structured and have defined roles and responsibilities.
> 
> - **Clubs**, on the other hand, are student-run organizations focused on promoting interests in specific domains such as technology, culture, sports, or hobbies. They are more activity-driven and are formed to provide students with opportunities to explore their passions, develop skills, and engage in extracurricular activities.
> 
> If you'd like a list of clubs at DAU, I can provide that as well. Let me know!
> 
> [Sources: 1, 2, 3, 4]

**Actual Answer (Expected)**:
> The 8 official SBG committees are: Academic, Annual Festival, Cafeteria Management, Cultural, Hostel Management, Sports, Student Placement, and Tech Support. Per the constitution, a Committee has an elected/selected membership tied to specific seat allocations per batch and votes in SBG meetings, while a Club is a voluntary-membership group (2-6 core members) formed around an extracurricular interest that gets one collective vote but does not have the same elected representation structure.

**Meta Data**:
- Category: club_committee_directory
- Latency: 20472 ms
- Response Words: 376
- Similarity Score: 47.06/100
- Pass/Fail: Pass

---
### Q00053: Explain the hierarchy between Student Body Government, committees and clubs.
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), the **Student Body Government (SBG)** is the overarching student-led administrative body responsible for representing and serving the student community. It operates through **committees** and **clubs**, each with distinct roles and responsibilities.
> 
> ### **1. Student Body Government (SBG)**
> The SBG is the primary governing body for students. It includes a **core team** with roles such as **Convener**, **Deputy Convener**, **Treasurer**, and **Secretary**. These individuals oversee the functioning of the SBG and its affiliated committees and clubs. For example, in the 2024-25 academic year, the SBG core team included:
> - **Convener:** Siddhant Gupta
> - **Deputy Convener:** Vivek Chaudhari
> - **Treasurer:** Yash Tarpara
> - **Secretary:** Pari Chauhan.
> 
> The SBG also includes **committees** and **hobby-driven clubs**. Specifically, the SBG comprises **8 committees** and **22 hobby-driven clubs**.
> 
> ---
> 
> ### **2. Committees**
> Committees are formal, structured bodies that focus on specific administrative or policy-related functions. They act as a bridge between the student community and the university administration. For example:
> - **Anti-Ragging Committee:** This committee includes a convener, deputy convener, treasurer, and secretary, along with student members who work to prevent ragging and ensure a safe campus environment.
> - **Academic Committee:** This committee serves as the interface between the student community and the institute administration for academic development.
> 
> Each committee is led by a **convener** and includes members who work on specific issues such as academics, welfare, or anti-ragging.
> 
> ---
> 
> ### **3. Clubs**
> Clubs are student-run organizations focused on **hobbies, interests, and extracurricular activities**. They are more informal in structure compared to committees and are driven by student interests. The SBG oversees **22 hobby-driven clubs**, which may include technical, cultural, sports, and media-based groups.
> 
> ---
> 
> ### **Hierarchy Overview**
> - **Student Body Government (SBG):** The top-level governing body.
>  - **SBG Core Team:** Manages the SBG and its operations.
>  - **8 Committees:** Handle specific administrative or policy-related functions.
>  - **22 Hobby-Driven Clubs:** Focus on extracurricular and interest-based activities.
> 
> This structure ensures that students have a platform to engage in both governance and personal development through a variety of roles and activities.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> The Student Body Government (SBG) is the overarching self-governing body comprising the members of all 8 committees, 21 clubs, and 3 affiliated organizations. Clubs and Committees are both answerable to SBG and draw part of their budget from it; Committees have elected representation and voting rights in SBG general meetings, while Clubs get one collective vote but no elected seats. The SBG Core Team can review a Club's work/budget use, and the Dean (Students) office oversees the SBG overall (e.g. mentoring the Election Commission).

**Meta Data**:
- Category: club_committee_directory
- Latency: 17179 ms
- Response Words: 341
- Similarity Score: 44.60/100
- Pass/Fail: Fail

---
### Q00054: I'm interested in AI, startups and research. Which three clubs should I join and why?
**Chatbot Answer**:
> Based on your interests in AI, startups, and research, here are three clubs you should consider joining at Dhirubhai Ambani University (DAU):
> 
> 1. **AI Club** 
>  This club is ideal for students interested in artificial intelligence. It provides a platform to explore AI concepts, engage in discussions, and participate in events related to the field. Joining the AI Club will help you connect with like-minded peers and deepen your understanding of AI technologies and applications.
> 
> 2. **DA-IICT Center for Entrepreneurship and Incubation** 
>  If you're interested in startups, this organization is a must-join. It supports students in developing entrepreneurial skills, ideating business ventures, and gaining insights into the startup ecosystem. The center also offers mentorship and resources to help students launch their ventures.
> 
> 3. **Research Club** 
>  For students passionate about research, the Research Club is an excellent choice. It encourages academic exploration, facilitates collaboration on research projects, and provides opportunities to present findings. This club will help you build a strong foundation in research methodologies and contribute to scholarly work.
> 
> These clubs align with your interests and will provide valuable opportunities for growth and engagement in AI, startups, and research.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> This is a reasoning/recommendation question rather than a single fact lookup. Based on the club directory, the most relevant matches are: AI Club (ai_club@dau.ac.in), Research Club (research_club@dau.ac.in), and Business Club (business_club@dau.ac.in) or DA-IICT Center for Entrepreneurship and Incubation for startups. A generated answer should draw on these clubs' listed contacts/mentors and be framed as a recommendation, not a verbatim fact.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 10141 ms
- Response Words: 190
- Similarity Score: 42.44/100
- Pass/Fail: Fail

---
### Q00055: I don't enjoy coding but like leadership and networking. Which clubs should I join?
**Chatbot Answer**:
> If you're interested in leadership and networking, here are some clubs at Dhirubhai Ambani University (DAU) that align with your interests:
> 
> 1. **Business Club** - This club provides a platform for students to develop skills in public relations, marketing, and sponsorship. It is ideal for those interested in leadership and networking opportunities.
> 
> 2. **Debate Club** - Engaging in debates enhances your communication and critical thinking skills while offering opportunities to interact with peers and professionals from various backgrounds.
> 
> 3. **Press Club** - The Press Club is a great place to improve your writing and communication skills while engaging with current affairs and networking with like-minded individuals.
> 
> 4. **Head Rush Quizzing Club** - This club fosters intellectual discussions and networking through quizzing events, which can be a fun way to connect with others who share your interests.
> 
> 5. **Cultural Committee** - If you enjoy organizing events and working with diverse groups, the Cultural Committee offers leadership roles in managing cultural festivals and events.
> 
> These clubs and committees provide excellent opportunities to develop leadership skills, build a professional network, and contribute to the vibrant student community at DAU.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Open-ended recommendation question. Non-technical/leadership-oriented options in the directory include Business Club, Press Club, The Debating Society, and committee roles (e.g. Academic Committee, Annual Festival Committee) which involve organizing and coordination rather than coding.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 10076 ms
- Response Words: 188
- Similarity Score: 35.52/100
- Pass/Fail: Fail

---
### Q00056: Compare AI Club, GDG and Programming Club across learning, projects, competitions and career value.
**Chatbot Answer**:
> The Artificial Intelligence Club (AI Club), Google Developers Group (GDG), and Programming Club at Dhirubhai Ambani University (DAU) offer distinct opportunities for students interested in technology, innovation, and career development. Here's a comparison across learning, projects, competitions, and career value:
> 
> ---
> 
> ### **1. Artificial Intelligence Club (AI Club)**
> - **Learning**: The AI Club focuses on hands-on learning, research collaboration, and community-driven projects. It offers workshops, hackathons, and speaker sessions to deepen understanding of AI fundamentals and advanced topics like computer vision, natural language processing, and deep learning.
> - **Projects**: Club members work on diverse projects, including building intelligent systems, predictive models, and exploring AI applications in real-world scenarios.
> - **Competitions**: While the AI Club does not explicitly mention specific competitions, it emphasizes collaborative problem-solving through hackathons and innovation challenges.
> - **Career Value**: The AI Club provides mentorship and exposure to emerging technologies, which are highly relevant for careers in AI, machine learning, and data science.
> 
> ---
> 
> ### **2. Google Developers Group (GDG)**
> - **Learning**: GDG on Campus DAU introduces students to the fundamentals of software development and open-source projects. It offers sessions to kickstart students' journeys in development and encourages engagement with the developer community.
> - **Projects**: GDG organizes Semester Long Projects (SLoP), an open-source initiative that introduces students to real-world software development and collaborative coding.
> - **Competitions**: GDG organizes events like Tic Tech Toe, a 48-hour hackathon aimed at fostering innovation and problem-solving.
> - **Career Value**: GDG provides exposure to open-source development, real-world coding practices, and collaboration with peers, which are valuable for careers in software engineering and development.
> 
> ---
> 
> ### **3. Programming Club**
> - **Learning**: The Programming Club focuses on coding and problem-solving through events like FizzBuzz, i.Relay, and BlindCode. These events help students enhance their technical expertise and problem-solving abilities.
> - **Projects**: The club provides a platform for students to showcase their coding skills and work on innovative solutions to technical challenges.
> - **Competitions**: The Programming Club participates in robotics and coding competitions such as Roboclash, i.Bot, and RoboSoccer, which test students' technical and creative abilities.
> - **Career Value**: The Programming Club is ideal for students aiming to build careers in software development, competitive programming, or tech innovation.
> 
> ---
> 
> ### **Summary**
> - **AI Club** is best for students interested in AI, machine learning, and research-driven projects.
> - **GDG** is ideal for those interested in open-source development, real-world coding, and collaboration with the developer community.
> - **Programming Club** is suited for students who enjoy competitive coding, problem-solving, and robotics challenges.
> 
> Each club offers unique opportunities to enhance technical and leadership skills, depending on a student's interests and career goals.
> 
> [Sources: 1, 3]

**Actual Answer (Expected)**:
> Comparison/reasoning question — the source only provides directory-level facts (convener, deputy convener, faculty mentor, email) for AI Club (ai_club@dau.ac.in, mentor Arpit Rana), Google Developer Groups (dsc@dau.ac.in, mentor Prof. Ankush Chander), and Programming Club (programming-club@dau.ac.in, mentor Prof. PM Jat). It does not contain activity/competition-level comparison data to ground a 'learning vs. projects vs. career value' judgment.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 20895 ms
- Response Words: 434
- Similarity Score: 40.30/100
- Pass/Fail: Fail

---
### Q00057: Compare Business Club and Research Club for someone planning to build a startup.
**Chatbot Answer**:
> For someone planning to build a startup, the **Business Club** and **Research Club** at Dhirubhai Ambani University (DAU) offer distinct but complementary opportunities. Here's a comparison based on their activities and relevance to entrepreneurship and research:
> 
> ### **Business Club**
> - **Key Activities**: The Business Club focuses on fostering entrepreneurial spirit and business acumen. It organizes discussions on innovative business ideas, trends, and strategies. Workshops, competitions, and networking events are central to its activities. These events aim to inspire creativity and provide practical knowledge about the corporate world.
> - **Startup Relevance**: The club is ideal for students interested in entrepreneurship. It offers a platform to explore business ideas, network with like-minded peers, and gain insights into the corporate landscape. For example, the club recently hosted an event titled "Dream, Dare, Do: The Startup Mindset," which directly aligns with startup-oriented thinking.
> - **Networking and Skill-Building**: The club emphasizes networking and skill-building, making it a hub for students who want to connect with industry professionals and learn about real-world business challenges.
> 
> ### **Research Club**
> - **Key Activities**: The Research Club is dedicated to exploring cutting-edge technologies and scientific research. It engages in activities such as research papers, tech talks, and collaborations with industry experts. The club encourages critical thinking and problem-solving, with a focus on fields like artificial intelligence, data science, and telecommunications.
> - **Startup Relevance**: While the Research Club is more research-oriented, it can be highly beneficial for students interested in tech-driven startups. The club's emphasis on interdisciplinary projects and industry collaborations can provide valuable insights and tools for developing innovative solutions.
> - **Skill Development**: The club cultivates a research-driven culture, which is essential for students aiming to build startups in technology or science-based fields. It encourages curiosity and knowledge-sharing, which are crucial for innovation.
> 
> ### **Comparison Summary**
> | Aspect | Business Club | Research Club |
> |--------|---------------|---------------|
> | **Focus** | Entrepreneurship, business acumen, networking | Research, technology, interdisciplinary projects |
> | **Startup Relevance** | High (directly supports entrepreneurial thinking and networking) | Moderate to high (supports innovation and tech-driven startups) |
> | **Activities** | Workshops, competitions, networking events | Research papers, tech talks, industry collaborations |
> | **Skill Development** | Business strategy, networking, practical corporate knowledge | Critical thinking, problem-solving, research methodology |
> 
> ### **Recommendation**
> If your primary goal is to build a startup, the **Business Club** is the most directly relevant due to its focus on entrepreneurship and networking. However, if your startup is tech-driven or research-based, the **Research Club** can provide valuable insights and tools. Joining both clubs could offer a well-rounded foundation for startup development, combining business acumen with technical and research expertise.
> 
> [Sources: 3, 4, 5]

**Actual Answer (Expected)**:
> Directory-level facts only: Business Club (business_club@dau.ac.in, convener Satvik Parihar, mentor Dr. Pankaj Kumar) vs. Research Club (research_club@dau.ac.in, convener Devdutt Dinesh, mentor Prof. Yash Vasavada). No activity-level detail is available in this corpus to substantiate a startup-fit comparison beyond these contacts.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 19395 ms
- Response Words: 439
- Similarity Score: 27.70/100
- Pass/Fail: Fail

---
### Q00058: Build a four-year extracurricular roadmap using clubs and committees.
**Chatbot Answer**:
> Creating a four-year extracurricular roadmap using clubs and committees at DAU can help students develop leadership, technical, and soft skills while aligning with their academic and career goals. Here's a structured roadmap based on the university's club and committee structure:
> 
> ---
> 
> ### **Year 1: Exploration and Foundation**
> **Objective:** Explore diverse interests, understand the club/committee ecosystem, and build foundational skills.
> 
> 1. **Join 2–3 clubs** to explore different interests:
>  - **Technical Clubs:** Artificial Intelligence Club, Programming Club, or Microsoft Student Technical Club to build technical skills and engage in coding competitions or hackathons.
>  - **Cultural Clubs:** Dance Club, Music Club, or Debate Club to develop creativity and public speaking skills.
>  - **Professional Clubs:** Business Club or Press Club to learn about marketing, public relations, and organizational management.
> 
> 2. **Attend university festivals** like i.Fest (technical), Concours (sports), and Synapse (cultural) to understand the university's extracurricular culture and identify areas of interest.
> 
> 3. **Consider joining a committee** like the Cultural Committee or Sports Committee to understand how large-scale events are organized and managed.
> 
> ---
> 
> ### **Year 2: Skill Development and Leadership**
> **Objective:** Deepen involvement in chosen clubs, take on leadership roles, and contribute to impactful projects.
> 
> 1. **Take on a leadership role** in one or more clubs (e.g., co-head of the Artificial Intelligence Club or a core member of the Debate Club) to develop leadership and project management skills.
> 
> 2. **Participate in inter-college competitions** organized by clubs like the Programming Club or Debate Club to gain exposure and build a competitive edge.
> 
> 3. **Join a specialized committee** such as the Academic Committee or Cafeteria Management Committee to understand administrative processes and contribute to student welfare.
> 
> 4. **Engage in collaborative projects** with other clubs or committees (e.g., organizing a joint event with the Cultural Committee and the Business Club) to enhance teamwork and cross-functional collaboration.
> 
> ---
> 
> ### **Year 3: Strategic Contribution and Networking**
> **Objective:** Make a significant impact in chosen clubs, build a professional network, and align extracurricular activities with career goals.
> 
> 1. **Lead a major project or event** in a club or committee (e.g., organizing a hackathon for the Artificial Intelligence Club or managing a cultural event for the Cultural Committee).
> 
> 2. **Collaborate with the Student Placement Cell** to understand industry expectations and align club activities with career goals (e.g., organizing a startup workshop with the Business Club).
> 
> 3. **Network with faculty and professionals** through club events, faculty appreciation awards, or guest lectures (e.g., attending talks by Prof. Vinay Palaparthy or Prof. Sreeja Rajendran).
> 
> 4. **Mentor first-year students** in clubs to reinforce your own knowledge and develop leadership and communication skills.
> 
> ---
> 
> ### **Year 4: Leadership and Legacy**
> **Objective:** Leave a lasting impact, refine leadership skills, and prepare for post-graduation opportunities.
> 
> 1. **Lead a club or committee** (e.g., head of the Artificial Intelligence Club or head of the Academic Committee) to manage large teams and drive strategic initiatives.
> 
> 2. **Organize a flagship event** (e.g., a major technical competition, cultural fest, or sports tournament) to showcase leadership and organizational skills.
> 
> 3. **Collaborate with the Placement Cell** to organize career-focused events (e.g., startup workshops, resume-building sessions) to support peers in their career journeys.
> 
> 4. **Document and share your experiences** through the university's media or club newsletters to create a legacy and inspire future students.
> 
> ---
> 
> ### **Additional Tips**
> - **Balance academics and extracurriculars** to maintain a strong GPA while gaining diverse experiences.
> - **Seek feedback** from faculty, club mentors, and peers to continuously improve your skills and contributions.
> - **Leverage university resources** like the Tech Support Committee or the Student Placement Cell for guidance and support.
> 
> By following this roadmap, students can build a well-rounded profile that enhances their academic journey and prepares them for future career opportunities.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Open-ended planning question; only the static club/committee directory and SBG seat-allocation table (by batch year) are available as grounding, not a ready-made 4-year roadmap.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 24485 ms
- Response Words: 614
- Similarity Score: 29.81/100
- Pass/Fail: Fail

---
### Q00059: Recommend the best combination of clubs for maintaining a high CPI while maximizing career opportunities.
**Chatbot Answer**:
> To maintain a high CPI while maximizing career opportunities, the best combination of clubs should balance academic focus with skill development and networking. Based on the retrieved information, here are the most suitable clubs and their benefits:
> 
> ### 1. **Business Club** 
> - **Key Activities:** Entrepreneurship discussions, workshops, and networking events. 
> - **Career Value:** Ideal for students interested in startups, business strategy, and leadership. The club provides opportunities to connect with industry professionals and gain insights into the entrepreneurial ecosystem. 
> - **Academic Balance:** The club's activities are structured to complement academic schedules, ensuring minimal disruption to studies. 
> - **Contact:** Gaurav Meena, [business_club@dau.ac.in](mailto:business_club@dau.ac.in)
> 
> ### 2. **Microsoft Student Technical Club (MSTC)** 
> - **Key Activities:** Open Source, Hacktoberfest, and Winter-of-Code (WoC) participation. 
> - **Career Value:** Offers hands-on experience in coding, open-source projects, and collaboration with global developers. This is highly valuable for students aiming for careers in software development, AI, or tech startups. 
> - **Academic Balance:** Events are often scheduled during weekends or after class hours, allowing students to manage their academic commitments effectively. 
> - **Contact:** Zeel Dadhaniya, [microsoftclub@dau.ac.in](mailto:microsoftclub@dau.ac.in)
> 
> ### 3. **Muse – The Designing Club** 
> - **Key Activities:** Design innovation and idea-sharing sessions. 
> - **Career Value:** Enhances creative and design thinking, which is increasingly valuable in tech and startup ecosystems. Muse helps students build a portfolio and connect with design professionals. 
> - **Academic Balance:** Activities are project-based and flexible, allowing students to manage their time efficiently. 
> - **Contact:** Preksha Shah, [muse@dau.ac.in](mailto:muse@dau.ac.in)
> 
> ### 4. **Headrush: Quizzing Club** 
> - **Key Activities:** Regular quizzes and the flagship I.Quiz event. 
> - **Career Value:** Quizzing hones critical thinking, general knowledge, and quick decision-making skills—useful in leadership and strategic roles. 
> - **Academic Balance:** Quizzing events are typically short and scheduled during breaks or weekends, ensuring minimal academic interference. 
> - **Contact:** Shashwat Menon, [quizzing@dau.ac.in](mailto:quizzing@dau.ac.in)
> 
> ### Academic Balance and Career Synergy 
> According to the **Student Clubs and Organisations Policy**, students can join multiple clubs as long as their academic performance is maintained. This means you can strategically choose clubs that align with your career goals while ensuring your academic focus remains intact. The clubs mentioned above offer a mix of technical, entrepreneurial, and creative opportunities, all while being structured to support academic priorities.
> 
> For more information on club policies or to reach out to the Dean (Students), visit the [Student Affairs Office](https://www.daiict.ac.in/dean-students) or contact the SBG Core Team.
> 
> [Sources: 1, 2, 4]

**Actual Answer (Expected)**:
> Open-ended reasoning question with no direct grounding on CPI-vs-extracurricular tradeoffs in the corpus. Note: Academic Committee membership specifically requires a minimum CPI of 7.0 and no current backlogs per the SBG Constitution.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 19357 ms
- Response Words: 391
- Similarity Score: 29.96/100
- Pass/Fail: Fail

---
### Q00060: Which clubs best complement an Electronics student and why?
**Chatbot Answer**:
> For an Electronics student at Dhirubhai Ambani University (DAU), the **Electronics Hobby Club (EHC)** is the most directly complementary club. It is specifically designed to help students explore and enjoy the world of electronics through hands-on projects and learning sessions. The club works with technologies like Arduino, Raspberry Pi, and NodeMCU, which are highly relevant to an Electronics student's academic and career interests. Additionally, the club organizes events like RC car races and open projects, providing opportunities to apply theoretical knowledge in practical settings. This aligns well with the academic goals of an Electronics student, offering a platform to experiment, innovate, and build real-world projects.
> 
> If the student is also interested in creative or hobby-based activities, the **Photography and Movie Making Club (PMMC)** could be a good secondary choice. While not directly related to electronics, it offers a creative outlet and helps students develop skills in photography and videography. These skills can be useful for documenting projects, creating promotional content for clubs, or even exploring multimedia as a side interest.
> 
> The **Chess Club** is another option for students interested in strategic thinking and problem-solving, which are valuable skills in engineering disciplines like Electronics. However, it is less directly aligned with the technical interests of an Electronics student compared to the EHC.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The clearest directory match is the Electronics Hobby Club (EHC, ehc@dau.ac.in, mentor Prof. Sujay Kadam); IEEE Student Branch DA-IICT (ieee@dau.ac.in) is also relevant as one of the three SBG-affiliated organizations.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 11559 ms
- Response Words: 213
- Similarity Score: 43.18/100
- Pass/Fail: Fail

---
### Q00061: Tell me about DAU's Aerospace Club.
**Chatbot Answer**:
> The **Sports Committee (DAUSC)** at Dhirubhai Ambani University (DAU) is one of the eight student committees under the Dean (Students) office. Its primary role is to promote fitness, teamwork, and sporting excellence among students. The committee organizes a range of events, including **Concours** (an inter-university sports tournament), **DCL (DAU Cricket League)**, **Inter-Wing Tournaments**, and **Freshers' Weekend**, which are designed to foster unity, friendly competition, and a vibrant campus culture.
> 
> The committee's vision is to establish DAU as a hub of sporting excellence, where students have access to high-quality facilities, expert guidance, and a supportive community to nurture their athletic potential. The current convener of the Sports Committee is **Ishan Thakkar**, and the deputy convener is **Ved Mungra**. You can contact the committee via email at **sports@dau.ac.in**.
> 
> It is important to note that the **Sports Committee** is distinct from the **Aerospace Club** or other student clubs. While the committee focuses on organizing sports-related events and promoting physical activity, the Aerospace Club (or any other club) would typically focus on technical or hobby-based activities. The clubs and committees operate independently but are both part of the broader student services ecosystem at DAU.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> No Aerospace Club appears in the official SBG club/committee list (21 clubs, 8 committees, 3 organizations, 1 dormant club) or anywhere else in this corpus. This looks like a trap/adversarial question — the correct answer is that no such club is documented, not a fabricated description.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 12505 ms
- Response Words: 194
- Similarity Score: 31.24/100
- Pass/Fail: Fail

---
### Q00062: Which club manages Formula Student at DAU?
**Chatbot Answer**:
> I could not find information about which club manages Formula Student at DAU in the available university data. For more specific or updated information, you may reach out to the Student Affairs or Extracurricular Activities department at DA-IICT. You can also visit the official website at https://www.daiict.ac.in for further assistance.

**Actual Answer (Expected)**:
> No Formula Student club or team appears anywhere in this corpus's club/committee directory. This is a trap/adversarial question — a correct system should state that no such club is documented rather than guessing.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 6327 ms
- Response Words: 50
- Similarity Score: 44.80/100
- Pass/Fail: Fail

---
### Q00063: Explain the Blockchain Club at DAU.
**Chatbot Answer**:
> The Blockchain Club at Dhirubhai Ambani University (DAU) is a technical student club that focuses on exploring and promoting blockchain technology and its applications. While the specific details of the Blockchain Club are not directly mentioned in the retrieved documents, the club is likely part of the broader technical and innovation ecosystem at DAU. This ecosystem includes clubs like the IEEE Student Branch and events such as Hackout’25, where blockchain was one of the technologies highlighted for addressing sustainability challenges.
> 
> Blockchain Club activities typically include:
> - **Educational Workshops and Seminars:** These sessions help students understand the fundamentals of blockchain, smart contracts, decentralized applications (dApps), and related technologies.
> - **Hackathons and Innovation Challenges:** Events like Hackout’25 provide a platform for students to apply blockchain in real-world problem-solving scenarios, such as sustainability and energy challenges.
> - **Collaborations and Industry Engagement:** The club may invite industry experts and professionals to share insights on blockchain trends, use cases, and career opportunities.
> - **Research and Development Projects:** Students may engage in blockchain-based projects, exploring applications in finance, supply chain, healthcare, and more.
> 
> The Blockchain Club aligns with DAU’s focus on innovation and interdisciplinary collaboration, offering students opportunities to develop technical and leadership skills while staying at the forefront of emerging technologies. For more detailed information about the club’s structure, leadership, or specific activities, you may need to reach out to the club directly or consult the university’s official website.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> No Blockchain Club appears in the official club list; the closest related entity is the Cyber Information and Network Security (CINS) Club. This is a trap/adversarial question testing whether the system fabricates a club that doesn't exist.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 11075 ms
- Response Words: 236
- Similarity Score: 49.47/100
- Pass/Fail: Pass

---
### Q00064: Who is the current convenor of Programming Club? Include official contact details if available.
**Chatbot Answer**:
> The current convenor of the Programming Club at Dhirubhai Ambani University (DAU) for the academic year 2026-27 is **Mahek Kanani**. The official contact details for the Programming Club are as follows:
> 
> - **Email Address:** programming-club@dau.ac.in 
> - **Convener Mobile Number:** 96015 94723 
> - **Faculty Mentor:** Prof. PM Jat 
> 
> For further communication, you can use the provided email or mobile number.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Per the 2026-27 club information sheet: Convener Mahek Kanani (Student ID 202403019), Deputy Convener Raj Patel (Student ID 202401152), Faculty Mentor Prof. PM Jat, official club email programming-club@dau.ac.in. (Personal phone numbers exist in the raw data but are withheld here for privacy.)

**Meta Data**:
- Category: club_committee_directory
- Latency: 8143 ms
- Response Words: 61
- Similarity Score: 53.36/100
- Pass/Fail: Pass

---
### Q00065: Which clubs are currently recruiting members?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, the following clubs are currently recruiting members for the Winter 2026 academic year:
> 
> 1. **Business Club** 
>  - Convenor: Rishi Patel 
>  - Deputy Convenor: Yuvansh Vaghasiya 
>  - Core Members: Satvik Parihar, Dhvanit Vaghela, Daksh Rathod 
> 
> 2. **Chess Club** 
>  - Convenor: Aarya Shah 
>  - Deputy Convenor: Kalp Shah 
>  - Core Members: Dweep Kotecha, Shubham Varmora, Krutant Jethva 
> 
> 3. **CINS Club** 
>  - Convener: Aalok Thakkar 
>  - Deputy Convener: Poorva Vaishnav 
>  - Core Members: Kasak Sutaria, Quincy Vadi 
> 
> These clubs are actively seeking members for their core teams, and interested students can reach out to the convenors or deputy convenors for more information about recruitment processes and timelines.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> This corpus is a static snapshot and does not contain live/current recruitment-status data; recruitment timing would need to come from a live source (SBG announcements, club social media) rather than this document set.

**Meta Data**:
- Category: club_logistics
- Latency: 9345 ms
- Response Words: 115
- Similarity Score: 40.10/100
- Pass/Fail: Fail

---
### Q00066: Which clubs completed recruitments most recently?
**Chatbot Answer**:
> The most recent recruitment updates for clubs at Dhirubhai Ambani University (DAU) are listed in the "List of Club Committee Core Members Winter 2026" document. Based on the information provided, the following clubs have completed their recruitment for the Winter 2026 academic year:
> 
> 1. **TSC (Technical Student Committee)** 
>  - **Convener:** Jainil Jagtap 
>  - **Deputy Convener:** Tirth Gandhi 
>  - **Core Members:** Yunus Kothari, Devarshi Dave
> 
> 2. **AI Club** 
>  - **Convenor:** Siddharth Rambhia 
>  - **Deputy Convenor:** Jainil Jagtap 
>  - **Core Members:** Devarsh Vasani, Vedant Shah, Aaditya Kaushik
> 
> 3. **Business Club** 
>  - **Convenor:** Rishi Patel 
>  - **Deputy Convenor:** Yuvansh Vaghasiya 
>  - **Core Members:** Satvik Parihar, Dhvanit Vaghela, Daksh Rathod
> 
> 4. **Chess Club** 
>  - **Convenor:** Aarya Shah 
>  - **Deputy Convenor:** Kalp Shah 
>  - **Core Members:** Dweep Kotecha, Shubham Varmora, Krutant Jethva
> 
> These clubs have finalized their core member lists for the Winter 2026 academic year, as per the latest available information.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No recruitment-timeline data is present in this static corpus; this would require a live/current-events source rather than the archived club directory files.

**Meta Data**:
- Category: club_logistics
- Latency: 12290 ms
- Response Words: 150
- Similarity Score: 26.08/100
- Pass/Fail: Fail

---
### Q00067: I missed orientation. Can I still join clubs?
**Chatbot Answer**:
> Yes, you can still join clubs even if you missed orientation. Students are allowed to join multiple clubs as long as their academic performance is maintained. There is no mention of orientation being a mandatory requirement for club membership in the retrieved documents. You can reach out to the **Student Affairs Office, DAU Campus, Gandhinagar**, or the **Dean (Students) / SBG Core Team** for assistance in joining clubs.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The SBG Constitution and orientation-program articles don't state a rule tying club membership eligibility to orientation attendance; no explicit policy on this was found in the corpus.

**Meta Data**:
- Category: club_logistics
- Latency: 6742 ms
- Response Words: 70
- Similarity Score: 48.30/100
- Pass/Fail: Pass

---
### Q00068: Is there a limit on the number of clubs a student can join?
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), there is no explicit limit on the number of clubs a student can join. The policy states that students can join multiple clubs as long as their academic performance is maintained. 
> 
> According to the SBG Constitution, the Student Body Government (SBG) includes 8 committees, 21 active clubs, and 3 organizations. While the policy does not specify a cap on club memberships, it is important to balance extracurricular involvement with academic responsibilities. 
> 
> For more information, you can contact the **Student Affairs Office** or reach out to the **Dean (Students)** or **SBG Core Team**.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No explicit cap on general club membership was found. What the constitution does state is that a student cannot hold more than one elected/selected position (e.g. Convener) across committees in a given term — contesting for more than one position is strictly prohibited.

**Meta Data**:
- Category: club_logistics
- Latency: 7786 ms
- Response Words: 100
- Similarity Score: 48.59/100
- Pass/Fail: Pass

---
### Q00069: Can first-year students become coordinators or convenors?
**Chatbot Answer**:
> First-year students can take on leadership roles in certain clubs and committees at DAU. For example, the Student Placement Cell (SPC) includes first-year students who are elected or selected to serve throughout their second year. These students manage tasks like mock interviews, coordinate with students and alumni, and handle interview logistics for placement candidates. The workload is significant, and first-year students often take on more responsibilities as senior members transition out during the placement cycle.
> 
> However, the specific eligibility for becoming a coordinator or convenor in other clubs may vary depending on the club's internal policies and recruitment processes. It is best to reach out to the respective club or committee for detailed information on leadership opportunities.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The constitution's committee seat-allocation table does allocate 1st-year seats on committees, and no blanket year-based restriction on becoming Convener is stated. The one explicit restriction found is for the Academic Committee specifically, which requires a minimum CPI of 7.0 and no current backlogs to contest — a bar a brand-new first-year student typically could not yet meet before their first grades are out.

**Meta Data**:
- Category: club_logistics
- Latency: 7950 ms
- Response Words: 119
- Similarity Score: 49.05/100
- Pass/Fail: Pass

---
### Q00070: I want to join the coding club.
**Chatbot Answer**:
> The **Programming Club** at Dhirubhai Ambani University (DAU) is dedicated to fostering a passion for competitive programming and equipping students with the skills to solve complex problems. Its vision is to position DAU as a hub for competitive programming by inspiring students to excel in the global coding community. The club also provides opportunities for students to participate in national and international coding competitions like the ACM ICPC and achieve high rankings on platforms such as Codeforces, CodeChef, LeetCode, and Atcoder.
> 
> If you're interested in joining the club, you can reach out to the current convener and deputy convener using the contact details provided:
> 
> - **Vraj K. Dobariya** - Convener 
> - **Devang S. Vaghani** - Deputy Convener 
> - **Email**: [programming-club[at]dau[dot]ac[dot]in](programming-club[at]dau[dot]ac[dot]in).
> 
> For more information about the club and its activities, you can also visit the university's official website.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> DAU does not have a club literally named 'Coding Club' — the closest matches in the official directory are Programming Club (programming-club@dau.ac.in) and Google Developer Groups On Campus (dsc@dau.ac.in). A good answer should clarify this rather than assume which one is meant.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 9955 ms
- Response Words: 139
- Similarity Score: 38.67/100
- Pass/Fail: Fail

---
### Q00071: Which is the best club at DAU?
**Chatbot Answer**:
> The concept of the "best" club at Dhirubhai Ambani University (DAU) depends on your personal interests and goals. However, based on the retrieved information, here are three clubs that stand out for their unique contributions and activities:
> 
> 1. **Research Club** 
>  The Research Club is ideal for students passionate about exploring cutting-edge technologies and scientific research. It fosters a research-driven culture through activities like research papers, tech talks, and collaborations with industry experts. The club focuses on fields such as artificial intelligence, data science, and telecommunications. 
>  - **Contact**: Gulafsha Bhatti (Convener), Dev Joshi (Deputy Convener) 
>  - **Email**: [research_club[at]dau[dot]ac[dot]in](mailto:research_club[at]dau[dot]ac[dot]in) 
>  - **Social Media**: [Instagram](https://www.instagram.com/research.club.daiict/), [Facebook](https://in.linkedin.com/company/research-club-daiict) 
> 
> 2. **Chess Club** 
>  The Chess Club is a hub for chess enthusiasts, aiming to foster a passion for the game and promote competitive spirit. The club organizes tournaments, fun events, and learning sessions for new enthusiasts. 
>  - **Contact**: Aarya Shah (Convener), Kalp Shah (Deputy Convener) 
>  - **Email**: [chess_club[at]dau[dot]ac[dot]in](mailto:chess_club[at]dau[dot]ac[dot]in) 
> 
> 3. **Electronics Hobby Club (EHC)** 
>  The EHC is perfect for students interested in hands-on electronics projects. The club encourages creativity and experimentation with technologies like Arduino, Raspberry Pi, and NodeMCU. It organizes events like RC car races and open projects, allowing students to build and showcase their skills. 
>  - **Contact**: Kaushik Prajapati (Convener), Parjanya Rajput (Deputy Convener) 
>  - **Email**: [ehc[at]dau[dot]ac[dot]in](mailto:ehc[at]dau[dot]ac[dot]in) 
> 
> Each of these clubs offers unique opportunities for learning, collaboration, and personal growth. You can explore their activities and leadership contacts to decide which aligns best with your interests and academic goals.

**Actual Answer (Expected)**:
> This is a subjective/opinion question with no factual ground truth in the corpus; a good system response should decline to rank and instead ask about the student's interests or list the clubs.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 15561 ms
- Response Words: 242
- Similarity Score: 35.29/100
- Pass/Fail: Fail

---
### Q00072: I like everything. Recommend clubs for me.
**Chatbot Answer**:
> Based on your interest in a wide range of activities, here is a curated list of clubs and committees at DAU that cater to diverse interests, from technical and academic to cultural and recreational:
> 
> ### **Technical & Academic Clubs**
> 1. **Programming Club** 
>  Ideal for students passionate about coding and problem-solving. It offers opportunities to participate in hackathons, coding competitions, and collaborative projects.
> 
> 2. **Microsoft Student Technical Club** 
>  A hub for students interested in Microsoft technologies, offering workshops, training, and networking opportunities with industry professionals.
> 
> 3. **Google Developer Groups (GDG) Ong-DA** 
>  Focused on Google technologies and open-source development, this club supports students in learning and contributing to innovative projects.
> 
> 4. **Artificial Intelligence Club** 
>  For students interested in AI, machine learning, and related technologies. The club organizes workshops, seminars, and competitions to foster innovation.
> 
> 5. **Research Club** 
>  Encourages students to engage in academic research and interdisciplinary projects. It provides a platform to explore and present research ideas.
> 
> 6. **Electronics Hobby Club** 
>  Perfect for students with a passion for electronics and hands-on projects. The club supports experimentation and innovation in electronic circuits and devices.
> 
> ---
> 
> ### **Cultural & Creative Clubs**
> 1. **Debate Club** 
>  Enhances public speaking, critical thinking, and argumentation skills. It organizes inter-college debates and workshops.
> 
> 2. **Head Rush Quizzing Club** 
>  For trivia enthusiasts, this club hosts quiz competitions and trivia nights, fostering a spirit of learning and fun.
> 
> 3. **THE MUSIC CLUB** 
>  A platform for students to explore and showcase their musical talents. It organizes performances and music-related events.
> 
> 4. **FILM CLUB** 
>  Encourages students to explore the art of filmmaking and storytelling. It hosts film screenings and workshops.
> 
> 5. **DA-IICT Theater Group** 
>  Offers opportunities to engage in theater, acting, and stage production. It organizes plays and performances.
> 
> 6. **Dance Club** 
>  For students interested in dance, this club provides training in various dance forms and organizes performances.
> 
> 7. **HERITAGE CLUB** 
>  Focuses on preserving and promoting cultural heritage through events, workshops, and educational activities.
> 
> ---
> 
> ### **Sports & Recreational Clubs**
> 1. **DA-IICT Khelaiya Club** 
>  Promotes sports and physical fitness. It organizes inter-college competitions and training sessions.
> 
> 2. **Chess Club** 
>  For students who enjoy strategic thinking and chess. It hosts tournaments and training sessions.
> 
> 3. **Cubing Club** 
>  A community for Rubik's cube enthusiasts. It organizes speed-cubing events and workshops.
> 
> ---
> 
> ### **Media & Communication Clubs**
> 1. **Press Club** 
>  Encourages students to develop writing and journalism skills. It produces newsletters and articles.
> 
> 2. **RADIO DAIICT** 
>  A student-run radio station that broadcasts music, interviews, and campus news.
> 
> 3. **Sambhav** 
>  A literary and creative writing club that fosters creativity through writing workshops and publications.
> 
> 4. **PHOTOGRAPHY MOVIE MAKING** 
>  For students interested in photography and videography. It offers training and opportunities to showcase work.
> 
> ---
> 
> ### **Committees**
> 1. **Academic Committee** 
>  Works on improving the academic environment and student experience.
> 
> 2. **Tech Support Committee** 
>  Provides technical support and solutions for campus-related issues.
> 
> 3. **Hostel Management Committee** 
>  Focuses on improving hostel facilities and student life.
> 
> 4. **Sports Committee** 
>  Organizes sports events and promotes physical fitness.
> 
> 5. **Cultural Committee** 
>  Plans and executes cultural events and festivals.
> 
> 6. **Student Placement Cell** 
>  Assists students with placements and career development.
> 
> These clubs and committees offer a wide range of opportunities to explore your interests, develop new skills, and connect with like-minded peers. You can join multiple clubs based on your interests and availability. If you're unsure where to start, consider attending club meetings or orientation sessions to get a better sense of what each club offers.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Open-ended; the full 21-club directory (student_faculty/sbg_constitution_25_26.md) is the relevant grounding for a broad recommendation, but there's no single 'correct' answer.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 24867 ms
- Response Words: 574
- Similarity Score: 13.04/100
- Pass/Fail: Fail

---
### Q00073: Give the official social media handles for every technical club.
**Chatbot Answer**:
> Here are the official social media handles for the technical clubs at Dhirubhai Ambani University (DAU), based on the available information:
> 
> 1. **Microsoft Student Technical Club (MSTC)** 
>  - [Facebook](https://www.facebook.com/mstcatdaiict)
> 
> Other technical clubs have not provided social media handles in the retrieved documents. For more information or to connect with these clubs, you can use their official email addresses:
> 
> - **Cyber Information and Network Security Club (CINS)** 
>  - Email: cins_club@dau.ac.in
> 
> - **Microsoft Student Technical Club (MSTC)** 
>  - Email: microsoftclub@dau.ac.in
> 
> If you need further assistance or details about other clubs, feel free to ask!
> 
> [Sources: 3, 4]

**Actual Answer (Expected)**:
> No social media handles are recorded in this corpus's club data — only official email addresses (e.g. ai_club@dau.ac.in, programming-club@dau.ac.in) are documented.

**Meta Data**:
- Category: club_committee_directory
- Latency: 8988 ms
- Response Words: 95
- Similarity Score: 45.41/100
- Pass/Fail: Pass

---
### Q00074: Provide the official contact information for Student Body Government.
**Chatbot Answer**:
> The official contact information for the **Student Body Government (SBG)** at Dhirubhai Ambani University (DAU) is as follows:
> 
> - **General Email:** sbg@dau.ac.in
> - **Convenor:** Yash Judal, Email: convener_student_government@dau.ac.in
> - **Deputy Convenor:** Dev Sanghani, Email: dy_convener_student_government@dau.ac.in
> - **Secretary:** Siddh Shah, Email: secretary_student_government@dau.ac.in
> - **Treasurer:** Madhav Bhatt, Email: treasurer_student_government@dau.ac.in
> 
> For general inquiries or communication with the SBG, the primary email is **sbg@dau.ac.in**. For specific roles or responsibilities, you can reach out to the respective office-bearer using their individual email addresses.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> The SBG Core Team (Tenure 25-26) is listed as: Convener Parshv Joshi, Deputy Convener Pratham Lakhani, Treasurer Bhavya Boda, Secretary Jayansh Gaadhe. A dedicated general SBG email address was not found in this corpus; individual club/committee emails (e.g. sbg_academics@dau.ac.in) are documented instead.

**Meta Data**:
- Category: club_committee_directory
- Latency: 9619 ms
- Response Words: 82
- Similarity Score: 43.99/100
- Pass/Fail: Fail

---
### Q00075: List all committees first, then list all clubs without duplicating any organization.
**Chatbot Answer**:
> Here is the list of committees and clubs at DA-IICT, organized without duplication:
> 
> ### Committees
> 1. Academic Committee 
> 2. Annual Festival Committee 
> 3. Cafeteria Management Committee 
> 4. Cultural Committee 
> 5. Hostel Management Committee 
> 6. Sports Committee 
> 7. Student Placement Committee 
> 8. Tech Support Committee 
> 
> ### Clubs
> 1. AI Club 
> 2. Business Club 
> 3. Chess Club 
> 4. Cubing Club 
> 5. Cyber Information and Network Security Club 
> 6. DA-IICT Theatres Group 
> 7. Dance Club 
> 8. Debate Club (The Debating Society) 
> 9. Google Developer Groups, On Campus, DA-IICT 
> 10. Electronics Hobby Club 
> 11. Film Club 
> 12. Headrush Quizzing Club 
> 13. Khelaiya Club 
> 14. Microsoft Student Technical Club 
> 15. Muse Club 
> 16. Music Club 
> 17. Photography and Movie Making Club 
> 18. Press Club 
> 19. Programming Club 
> 20. Radio Club 
> 21. Research Club 
> 
> ### Dormant Clubs
> 1. Heritage Club 
> 
> ### Organizations
> 1. DA-IICT Center for Entrepreneurship and Incubation 
> 2. IEEE Student Branch DA-IICT 
> 3. Sambhav 
> 
> This information is based on the academic year **2025-26**.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Committees (8): Academic, Annual Festival, Cafeteria Management, Cultural, Hostel Management, Sports, Student Placement, Tech Support. Clubs (21): AI Club, Business Club, Chess Club, Cubing Club, Cyber Information & Network Security Club, DA-IICT Theatres Group, Dance Club, The Debating Society, GDG On Campus, Electronics Hobby Club, Film Club, Headrush Quizzing Club, Khelaiya Club, Microsoft Student Technical Club, Muse Club, Music Club, Photography & Movie Making Club, Press Club, Programming Club, Radio Club, Research Club. (Separately: 3 organizations — DA-IICT CEI, IEEE Student Branch, Sambhav; 1 dormant club — Heritage Club.)

**Meta Data**:
- Category: club_committee_directory
- Latency: 10987 ms
- Response Words: 161
- Similarity Score: 80.66/100
- Pass/Fail: Pass

---
### Q00076: Which clubs participated in orientation? Mention the source of your answer.
**Chatbot Answer**:
> The clubs that participated in orientation are not explicitly listed in the provided documents. However, the documents mention clubs and their activities, which are part of the broader student club culture at DAU. For example, clubs like the **Khelaiya Club**, **Cubing Club**, **Radio Club**, **Chess Club**, **Electronics Hobby Club**, and **Research Club** are mentioned in the context of their activities and convenors. 
> 
> If you are referring to clubs that are active and likely to participate in orientation, the **Placement Brochure 2025-26** lists a comprehensive list of clubs at DAU, including the **Programming Club**, **Microsoft Student Technical Club**, **Google Developer Groups Ong-DA**, **Business Club**, **Debate Club**, **Artificial Intelligence Club**, **Radio DAIICT**, **Heritage Club**, **Chess Club**, **Press Club**, **Sambhav**, **The Music Club**, **Khelaiya Club**, **Cubing Club**, **Electronics Hobby Club**, and **DA-IICT Theater Group**, among others.
> 
> For the most accurate and up-to-date information on which clubs participated in orientation, you may need to consult the **Dean (Students)** office or the **Placement Cell** at Dhirubhai Ambani University. You can visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in) for further details.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> The orientation-program news articles describe general sessions (academics, hostel, alumni interactions, ICT resources, ICC orientation) but do not name specific participating clubs — no club-level orientation-participation data was found.

**Meta Data**:
- Category: club_committee_directory
- Latency: 12387 ms
- Response Words: 178
- Similarity Score: 31.10/100
- Pass/Fail: Fail

---
### Q00077: Create a semester-wise extracurricular plan balancing academics, clubs and internships.
**Chatbot Answer**:
> Creating a balanced semester-wise extracurricular plan for a B.Tech (ICT) student at DAU involves aligning academic requirements, club participation, and internships. Based on the academic calendar and program structure outlined in the retrieved documents, here is a suggested plan:
> 
> ---
> 
> ### **Semester 1**
> **Academic Focus:**
> - Foundation courses in Computer Science, Information Technology, Mathematics, and Basic Sciences.
> - Introduction to ICT skills.
> 
> **Extracurricular Plan:**
> - **Join 1-2 clubs:** Start exploring clubs aligned with your interests (e.g., Programming Club, Blockchain Club, or Aerospace Club). These clubs offer opportunities to engage in technical projects and events.
> - **Participate in co-curricular activities:** These include sports, cultural, and technical club activities. These are graded Pass/Fail and run over the first four semesters.
> 
> **Internship/Project:**
> - No internships during this semester.
> 
> ---
> 
> ### **Semester 2**
> **Academic Focus:**
> - Continue with foundation courses and begin elective exploration.
> 
> **Extracurricular Plan:**
> - **Continue club participation:** Deepen your involvement in the clubs you joined in Semester 1.
> - **Join an exploration project:** Work in groups of 8–10 under a faculty mentor to identify and solve real-world problems using ICT skills. This project spans Semesters 2 and 3 and is graded Pass/Fail.
> 
> **Internship/Project:**
> - No internships during this semester.
> 
> ---
> 
> ### **Semester 3**
> **Academic Focus:**
> - Continue with foundation courses and start elective courses.
> - Begin preparation for the rural internship.
> 
> **Extracurricular Plan:**
> - **Continue club and exploration project involvement.**
> - **Rural Internship (Winter Break):** Mandatory internship at an NGO or Government Organization during the winter break after the 3rd semester.
> 
> **Internship/Project:**
> - **Rural Internship:** This is a mandatory 1–2 week internship during the winter break after the 3rd semester.
> 
> ---
> 
> ### **Semester 4**
> **Academic Focus:**
> - Continue with foundation courses and elective courses.
> - Prepare for the industrial/research internship.
> 
> **Extracurricular Plan:**
> - **Continue club and exploration project involvement.**
> - **Begin planning for the industrial/research internship.**
> 
> **Internship/Project:**
> - No internships during this semester.
> 
> ---
> 
> ### **Semester 5**
> **Academic Focus:**
> - Focus on elective courses and project preparation.
> 
> **Extracurricular Plan:**
> - **Continue club participation.**
> - **Plan for the industrial/research internship.**
> 
> **Internship/Project:**
> - No internships during this semester.
> 
> ---
> 
> ### **Semester 6**
> **Academic Focus:**
> - Finalize elective courses and prepare for the industrial/research internship.
> 
> **Extracurricular Plan:**
> - **Continue club participation.**
> 
> **Internship/Project:**
> - **Industrial/Research Internship (Summer Break):** A 6–8 week mandatory internship during the summer break after the 6th semester. Choose between an industrial internship or a research internship based on your career goals.
> 
> ---
> 
> ### **Semester 7**
> **Academic Focus:**
> - Begin the BTech Project (BTP) or Industrial Training Project (ITP).
> 
> **Extracurricular Plan:**
> - **Continue club participation.**
> - **Participate in co-curricular activities.**
> 
> **Internship/Project:**
> - **BTech Project (BTP) or Industrial Training Project (ITP):** A semester-long project that demonstrates your ability to learn current areas of research or industrial interest. You can choose between on-campus or off-campus modes.
> 
> ---
> 
> ### **Semester 8**
> **Academic Focus:**
> - Finalize the BTech Project (BTP) or Industrial Training Project (ITP).
> 
> **Extracurricular Plan:**
> - **Continue club participation.**
> - **Participate in co-curricular activities.**
> 
> **Internship/Project:**
> - **Complete the BTech Project (BTP) or Industrial Training Project (ITP).**
> 
> ---
> 
> ### **Time Management Tips**
> 1. **Prioritize Academics:** Ensure that your academic workload is managed effectively, especially during the first four semesters when foundation courses are offered.
> 2. **Balance Club Participation:** Limit club involvement to 1–2 clubs to avoid overcommitment.
> 3. **Plan Internships in Advance:** Start preparing for internships early, especially the mandatory rural and industrial/research internships.
> 4. **Use Breaks for Internships:** Utilize the winter and summer breaks for internships to avoid conflicts with academic schedules.
> 5. **Leverage Exploration Projects:** These projects provide hands-on experience and can complement your academic learning.
> 
> This plan ensures a balanced approach to academics,
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Open-ended planning task; grounding would draw on the Academic Calendar (semester structure) and the club/committee directory, but there's no single correct plan documented.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 27186 ms
- Response Words: 604
- Similarity Score: 42.06/100
- Pass/Fail: Fail

---
### Q00078: For every recommendation, distinguish official DAU information from your own reasoning.
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), official information is derived from documented policies, reports, and administrative records. For example, the Annual Report 2023-24 provides audited financial and administrative details of the university. This includes information about faculty, programs, and institutional governance.
> 
> **Official DAU Information** refers to data explicitly stated in such documents. For instance:
> - The list of faculty members.
> - The audit and financial reporting procedures.
> - The responsibilities of management and governance bodies.
> 
> **My Reasoning** is based on general knowledge and logical interpretation, and it does not include any unverified or speculative information about DAU. For example:
> - I can suggest that students should balance academics and extracurriculars for holistic development, but this is not a policy from DAU.
> - I can recommend exploring clubs like the Programming Club or Blockchain Club based on their documented activities, but the specific benefits or experiences are not sourced from DAU documents.
> 
> **Responsibility for Official Information** lies with the university's administration and the documented policies. For example, the Annual Report 2023-24 is an official document that outlines the university's financial and administrative status. For the most accurate and up-to-date information, students and faculty should refer to the official DAU website or contact the relevant administrative offices directly.
> 
> If you have a specific question or need further clarification, feel free to ask!
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> This is an instruction about response format rather than a factual query; there is no single ground-truth 'answer' to evaluate against a source document.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 11294 ms
- Response Words: 221
- Similarity Score: 24.85/100
- Pass/Fail: Fail

---
### Q00079: Assume my interests are Machine Learning, debating and entrepreneurship. Recommend an optimal club strategy.
**Chatbot Answer**:
> Based on your interests in **Machine Learning**, **debating**, and **entrepreneurship**, here is an optimal club strategy tailored to your preferences, using the information from the retrieved documents:
> 
> ---
> 
> ### **1. Machine Learning**
> **Recommended Club: SIG Machine Intelligence**
> - **Description:** This club is ideal for students interested in Machine Learning and AI. It offers bi-weekly hands-on sessions for beginners and shares reading materials and video lectures to support progressive learning. Additionally, it plans to initiate group projects with mentors to apply theoretical knowledge practically.
> - **Activities:** Collaborative projects, discussions, and mentorship opportunities.
> - **Contact:** The club is part of the IEEE Student Branch, and you can reach out to them for more information.
> 
> ---
> 
> ### **2. Entrepreneurship**
> **Recommended Club: Business Club**
> - **Description:** The Business Club organizes events focused on entrepreneurship, such as "Entrepreneurship: In the Age of AI" and "Dream, Dare, Do: The Startup Mindset." These events provide insights into the entrepreneurial ecosystem and foster a mindset for innovation.
> - **Activities:** Events, workshops, and discussions on startup ideas and business strategies.
> - **Contact:** You can reach the Business Club via **business_club@dau.ac.in**.
> 
> ---
> 
> ### **3. Debating**
> While there is no specific club mentioned in the retrieved documents related to debating, you can consider the following options:
> - **General Strategy:** Join the **Student Body Government (SBG)** or engage with the **technical clubs** (like SIG Machine Intelligence) to participate in discussions and debates on relevant topics.
> - **Alternative:** If the SBG or technical clubs do not meet your debating needs, you can explore external opportunities or propose a new debating initiative within the SBG or a club.
> 
> ---
> 
> ### **Summary of Recommendations**
> | Interest | Recommended Club | Key Activities | Contact |
> |----------|------------------|----------------|---------|
> | Machine Learning | SIG Machine Intelligence | Bi-weekly sessions, collaborative projects | IEEE Student Branch |
> | Entrepreneurship | Business Club | Events like "Entrepreneurship: In the Age of AI" | business_club@dau.ac.in |
> | Debating | SBG or Technical Clubs | Discussions and debates on relevant topics | Explore SBG or propose new initiatives |
> 
> ---
> 
> ### **Additional Tips**
> - **Engage with Multiple Clubs:** You can join both SIG Machine Intelligence and the Business Club to explore both technical and entrepreneurial interests.
> - **Stay Active in Events:** Attend events organized by the Business Club to network with like-minded individuals and gain insights into the startup ecosystem.
> - **Propose New Initiatives:** If you find a gap in the current offerings, consider proposing new events or initiatives within the SBG or clubs to align with your interests.
> 
> This strategy balances your interests while leveraging the resources available at DAU.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Best directory matches: AI Club (ML), The Debating Society (debate_club@dau.ac.in, debating), and Business Club or DA-IICT Center for Entrepreneurship and Incubation (entrepreneurship). This remains a reasoning/recommendation task, not a single-fact lookup.

**Meta Data**:
- Category: club_recommendation_reasoning
- Latency: 18367 ms
- Response Words: 432
- Similarity Score: 41.80/100
- Pass/Fail: Fail

---
### Q00080: List every inactive or dissolved club at DAU and explain why it became inactive.
**Chatbot Answer**:
> I could not find information about inactive or dissolved clubs at Dhirubhai Ambani University (DAU) in the available university data. The retrieved documents only provide details about active clubs and their activities. For further assistance, you may contact the Dean (Students) office at DAU or visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> The SBG Constitution lists exactly one Dormant Club: Heritage Club. Per the constitution's Dormant Clubs rule, a club becomes dormant if it fails to attend two consecutive SBG general meetings, sends no mailer in an academic year, and performs no club activity — the corpus doesn't state which specific reason applied to Heritage Club.

**Meta Data**:
- Category: club_committee_directory
- Latency: 7857 ms
- Response Words: 51
- Similarity Score: 42.79/100
- Pass/Fail: Fail

---
### Q00081: List every upcoming event at DAU in chronological order.
**Chatbot Answer**:
> Here is a list of upcoming events at Dhirubhai Ambani University (DAU) in chronological order, along with registration or schedule details where available:
> 
> 1. **DAU Alumni Reconnect and Reunion** 
>  - **Date:** 03/05/2025 
>  - **Time:** 10:00 AM – 5:00 PM 
>  - **Details:** No specific registration schedule mentioned.
> 
> 2. **One Day Interactive Workshop on Design Thinking and The Business of AI** 
>  - **Date:** 03/05/2025 
>  - **Time:** 10:00 AM – 5:00 PM 
>  - **Details:** No specific registration schedule mentioned.
> 
> 3. **Celebrate International Yoga Day at DAU!** 
>  - **Date:** 21/06/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 4. **Workshop on Speech and Audio Signal Processing using FPGA** 
>  - **Date:** 16/06/2025 – 20/06/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 5. **Workshop on Arduino and FPGA Based Embedded System Design** 
>  - **Date:** 23/06/2025 – 27/06/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 6. **Academic Bank of Credit: Interactive Student Session** 
>  - **Date:** 29/07/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 7. **DAU commemorates the 5-year Milestone of NEP 2020 with Events on Indian Knowledge Systems** 
>  - **Date:** 01/08/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 8. **Formal Methods Update Meeting 2025** 
>  - **Date:** 03/07/2025 – 04/07/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 9. **Annual Conference of ISMMACS and the International Conference on Differential Equations** 
>  - **Date:** 07/12/2025 – 10/12/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 10. **Silver Jubilee Celebrations and Alumni Reunion: Honouring 25 Years of Excellence** 
>  - **Date:** 27/12/2025 – 28/12/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 11. **DAU to organize a Symposium on Pedagogies in Engineering Education** 
>  - **Date:** 15/11/2025 
>  - **Details:** No specific registration schedule mentioned.
> 
> 12. **Winter School on AI-Infused Software Engineering Research and Practice (AISE)** 
>  - **Date:** 07/01/2026 – 10/01/2026 
>  - **Details:** No specific registration schedule mentioned.
> 
> 13. **DAU to organise the 8th International Conference on Complex Dynamical Systems and Applications** 
>  - **Date:** 23/01/2026 – 26/01/2026 
>  - **Details:** No specific registration schedule mentioned.
> 
> For events related to admissions and registration for the academic year 2026-2027, the following schedule is outlined:
> 
> - **Filling of online Application Forms commences on:** 24 March 2026 
> - **On-line application closes on (Revised):** 22 June 2026 
> - **Announcement of Merit List:** TBD 
> - **Fees Payment window for shortlisted candidates:** TBD 
> - **Announcement of Admission Status:** TBD 
> - **Registration and document verification at DAU campus:** 20 July 2026 *(Tentative)* 
> - **Orientation Program:** 21-24 July 2026 *(Tentative)* 
> - **Commencement of Classes:** 27 July 2026 *(Tentative)* 
> 
> Please note that dates marked as tentative or TBD are subject to change. For the most accurate and up-to-date information, I recommend visiting the official DAU website or contacting the university directly.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> This corpus is a static archive of past/announced event pages (not a live feed), so a definitive 'upcoming, chronologically ordered' list cannot be produced from it as of any given query date; a live events-page fetch would be needed.

**Meta Data**:
- Category: event_listing
- Latency: 27072 ms
- Response Words: 436
- Similarity Score: 18.33/100
- Pass/Fail: Fail

---
### Q00082: Which workshops are scheduled this month?
**Chatbot Answer**:
> Based on the information retrieved from the university knowledge base, here are the workshops scheduled this month (February 2025) along with their registration and schedule details:
> 
> 1. **Workshop on Data Analysis using Python** 
>  - **Date:** 24/06/2024 - 28/06/2024 
>  - **Details:** This workshop will cover the fundamentals of data analysis using Python. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> 2. **Workshop on Artificial Intelligence and its Applications in VLSI Design and Technology** 
>  - **Date:** 17/06/2024 - 21/06/2024 
>  - **Details:** This workshop will explore the applications of AI in VLSI design and technology. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> 3. **Summer School on Speech Signal Processing (S4P) on Automatic Speech Recognition** 
>  - **Date:** 06/07/2024 - 10/07/2024 
>  - **Details:** This summer school will focus on automatic speech recognition and related topics in speech signal processing. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> 4. **One-Day Workshop on Exploring Differential Equations through MATLAB: Applications** 
>  - **Date:** 03/01/2025 - 03/01/2025 
>  - **Details:** This workshop will explore differential equations through MATLAB and their applications. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> 5. **Teacher’s Enrichment Workshop (TEW) on Ordinary Differential Equations, Dynamical Systems, and Applications** 
>  - **Date:** 04/01/2025 - 09/01/2025 
>  - **Details:** This workshop is designed for teachers and will cover ordinary differential equations, dynamical systems, and their applications. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> 6. **Summer School on Speech Signal Processing (S4P) - July 05-09, 2025** 
>  - **Date:** 05/07/2025 - 09/07/2025 
>  - **Details:** This summer school will focus on speech signal processing. 
>  - **Registration:** Specific registration details are not provided in the retrieved data. For registration, you may need to check the official DA-IICT website or contact the organizing committee. 
> 
> For more information and registration details, you can visit the official DA-IICT website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> Time-dependent question that the static archive cannot answer definitively; individual workshop files (e.g. events/workshops/) have their own dates but there's no 'current month' filter possible against a fixed snapshot.

**Meta Data**:
- Category: event_listing
- Latency: 20743 ms
- Response Words: 395
- Similarity Score: 25.21/100
- Pass/Fail: Fail

---
### Q00083: Which hackathons are officially announced?
**Chatbot Answer**:
> I could not find information about hackathons or their registration schedules in the provided documents. For detailed information, I recommend visiting the official DAU website or contacting the Annual Festival Committee directly. You can reach out to them via the Student Body Government or the SBG & Clubs office for assistance. 
> 
> For more information, visit: [DAU Official Website](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> The corpus documents HackOut'25 (12th edition, Aug 29-31 2025, 72-hour hackathon under Synapse'26, themed on Blue Carbon Ecosystem and Green Hydrogen Fuel) as one officially reported hackathon; other past hackathon reports (e.g. SBG Hackout'24 event report) also exist in student_faculty/.

**Meta Data**:
- Category: event_listing
- Latency: 6570 ms
- Response Words: 58
- Similarity Score: 43.85/100
- Pass/Fail: Fail

---
### Q00084: Which seminars are currently open for registration?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, here are the seminars and events currently open for registration or scheduled in the near future:
> 
> 1. **Summer School on Speech Signal Processing (S4P) - July 05-09, 2025** 
>  - **Date:** 05/07/2025 - 09/07/2025
> 
> 2. **IEEE Lecture Series on 2D Materials for Nanoelectronics** 
>  - **Date:** 26/12/2024 - 26/12/2024
> 
> 3. **ACM India Winter School 2024 at DA-IICT** 
>  - **Date:** 16/12/2024 - 24/12/2024
> 
> 4. **One-Day Workshop on Exploring Differential Equations through MATLAB: Application** 
>  - **Date:** 03/01/2025 - 03/01/2025
> 
> 5. **Teacher’s Enrichment Workshop (TEW) on Ordinary Differential Equations, Dynamical Systems** 
>  - **Date:** 04/01/2025 - 09/01/2025
> 
> 6. **One Day Symposium on Complex Systems** 
>  - **Date:** 24/10/2024 - 24/10/2024
> 
> 7. **The IEEE Smart Village Symposium, an international conference** 
>  - **Date:** 07/11/2024 - 08/11/2024
> 
> 8. **DA-IICT PUBLIC LECTURE SERIES** 
>  - **Date:** 04/09/2024 - 04/09/2024
> 
> 9. **Workshop on Data Analysis using Python** 
>  - **Date:** 24/06/2024 - 28/06/2024
> 
> 10. **Workshop on Artificial Intelligence and its Applications in VLSI Design and Technology** 
>  - **Date:** 17/06/2024 - 21/06/2024
> 
> 11. **Summer School on Speech Signal Processing (S4P) on Automatic Speech Recognition** 
>  - **Date:** 06/07/2024 - 10/07/2024
> 
> 12. **Symposium Concept Note: Debating the Digital Transition: Society, Politics, Culture** 
>  - **Date:** 09/04/2024 - 09/04/2024
> 
> 13. **Book talk by Dr. Janaki Srinivasan (IIIT Bangalore) about her recent book, The People's Algorithm** 
>  - **Date:** 08/04/2024 - 08/04/2024
> 
> 14. **Public Lecture: Robots that learn by physically interacting with their surroundings** 
>  - **Date:** 04/04/2024 - 04/04/2024
> 
> 15. **Two-Day School on AI and Law, DA-IICT, Gandhinagar** 
>  - **Date:** 05/04/2024 - 06/04/2024
> 
> 16. **ITSS Workshop at DA-IICT** 
>  - **Date:** 16/03/2024 - 16/03/2024
> 
> 17. **Public lecture on Optimization: Theory and Practice** 
>  - **Date:** 14/03/2024 - 14/03/2024
> 
> 18. **BIRD STORIES: Classification, Conservation and Communication Design seminar** 
>  - **Date:** 15/03/2024 - 15/03/2024
> 
> 19. **Workshop on Digital Psychology: Harnessing Smartphone-Mediated Tools to Assess Mental Health** 
>  - **Date:** 16/03/2024 - 17/03/
> 
> [Sources: 6254, 6256, 6286, 6298, 6323, 6367, 6368, 6372, 6411, 6412, 6518, 6525, 6532, 6533, 6562, 6578, 6583, 6620]

**Actual Answer (Expected)**:
> Registration-open status is time-sensitive and not something a static document snapshot can confirm as 'currently' true.

**Meta Data**:
- Category: event_listing
- Latency: 27516 ms
- Response Words: 324
- Similarity Score: 12.71/100
- Pass/Fail: Fail

---
### Q00085: Summarize the important events from the academic calendar.
**Chatbot Answer**:
> Here is a summary of the important events from the academic calendar and registration schedule for the academic year 2026-27:
> 
> ### Academic Calendar 2026-27 (Admissions & Registration)
> - **Filling of online Application Forms commences on**: 24 March 2026.
> - **On-line application closes on (Revised)**: 22 June 2026.
> - **Announcement of Merit List**: TBD.
> - **Fees Payment window for shortlisted candidates**: TBD.
> - **Announcement of Admission Status**: TBD.
> - **Registration and document verification at DAU campus**: 20 July 2026 *(Tentative)*.
> - **Orientation Program**: 21-24 July 2026 *(Tentative)*.
> - **Commencement of Classes**: 27 July 2026 *(Tentative)*.
> 
> > Please note that dates marked as tentative or TBD are subject to change. Regular updates will be provided as the admission cycle progresses.
> 
> ### Academic Calendar (Summer 2026-27)
> - **M.Sc (AA) Project presentation**: 07 May 2027.
> - **M.Tech Minor Project presentation**: 12 May 2027.
> - **Registration for Summer 2026-27**: 12 May 2027 to 20 May 2027.
> - **Last date for submission of Results to Registrar’s Office**: 17 May 2027.
> - **Announcement of Results**: 18 May 2027.
> - **Commencement of Classes and Internships**: 24 May 2027.
> - **Research - Industrial Internship period**: 21 May 2027 to 09 July 2027.
> - **End-Semester Examination**: 10 July 2027 to 14 July 2027.
> - **M.Tech Major Project-1 presentation (Summer)**: 13 July 2027 to 15 July 2027.
> - **Announcement of Results**: 19 July 2027.
> - **Registration for Autumn 2027-28**: 05 July 2027 to 16 July 2027.
> - **Commencement of Session for Autumn 2027-28**: 19 July 2027.
> 
> For more details, you can visit the [DAU Academic Calendar page](https://daiict.ac.in/academic-calendar) or the [DAU website](https://www.daiict.ac.in).
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Key Autumn 2026-27 dates: Registration window 6-17 July 2026; Classes commence 22 July 2026; Add-Drop window 23-28 July 2026; 1st In-Semester Exam 31 Aug-5 Sep 2026; 2nd In-Semester Exam 6-10 Oct 2026; End-Semester Exam 23 Nov-2 Dec 2026; Results announced 14 Dec 2026.

**Meta Data**:
- Category: event_listing
- Latency: 17682 ms
- Response Words: 263
- Similarity Score: 50.95/100
- Pass/Fail: Pass

---
### Q00086: Recommend events for someone interested in AI and entrepreneurship.
**Chatbot Answer**:
> For someone interested in AI and entrepreneurship, here are the events recommended based on the retrieved information:
> 
> 1. **Event: Entrepreneurship: In the Age of AI** 
>  - Organized by the Business Club. 
>  - **Event Date:** July 29, 2025. 
>  - This event explores the intersection of AI and entrepreneurship, making it ideal for individuals interested in both domains. 
>  - **Event Report:** [Link](https://docs.google.com/document/d/17CcJCEAWdI-6Ib6XbFasdMZOSwXNydg9rI_709KL9Nw/edit?usp=sharing) 
>  - **Participants List:** [Link](https://docs.google.com/spreadsheets/d/1iD5AzJIHNjXNx0EbVeEAt3J23XgCCljKQqx0uAcRjmg/edit?usp=sharing) 
>  - **Event Photos:** [Link](https://drive.google.com/drive/folders/1vegMFIr44mO2M1k54uLkDv_z3-YCwubW) 
> 
> 2. **Event: Dream, Dare, Do: The Startup Mindset** 
>  - Also organized by the Business Club. 
>  - **Event Date:** July 23, 2025. 
>  - This event focuses on cultivating a startup mindset, which aligns with entrepreneurial interests. 
>  - **Event Report:** [Link](https://docs.google.com/document/d/1tvPvp1Wsvodc13QNiQX6QaM3EPhanPQOxsY-t44gCnA/edit?tab=t.0#heading=h.7jav6emv2rsa) 
>  - **Participants List:** [Link](https://docs.google.com/spreadsheets/d/1W3PypsEcAOg1LBo2CGMYd0wysm_LEoDabvg8FFasl54/edit?gid=1749030158#gid=1749030158) 
>  - **Event Photos:** [Link](https://drive.google.com/drive/folders/1fTTckAq8xm5Fz-H8z03eZNZfLmQkBU53?usp=sharing) 
> 
> Both events are institutional-level and were organized in the academic year 2025-26. If you are interested in registering for these events, you can contact the Business Club at **business_club@dau.ac.in** for further details.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Relevant documented events include the Two-Day Workshop on AI Engineering Bootcamp 2026, the One-Day Interactive Workshop on Design Thinking and the Business of AI, and HackOut'25 (innovation/entrepreneurship-themed hackathon) — but selecting a personalized 'best fit' is a reasoning task, not a single fact.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 17632 ms
- Response Words: 149
- Similarity Score: 26.00/100
- Pass/Fail: Fail

---
### Q00087: I only have two free hours every week. Which events should I prioritize?
**Chatbot Answer**:
> Given that you have only two free hours per week, it is important to prioritize events that align with your interests and offer the most value in terms of learning, networking, and skill development. However, the documents retrieved do not provide information about specific events or their schedules. They only contain academic course details for IE403 Human Computer Interaction and IE402 Optimization for the 2026-27 academic year.
> 
> To make the most of your limited time, consider the following general strategy:
> 
> 1. **Align with Academic Interests**: If you are interested in AI or entrepreneurship, prioritize events that offer workshops, seminars, or guest lectures related to these topics. These events often provide actionable insights and opportunities to connect with experts in the field.
> 
> 2. **Short and Impactful Events**: Look for events that are short in duration but high in impact, such as 1-hour webinars, mini-workshops, or panel discussions. These can be ideal for someone with limited time.
> 
> 3. **Skill-Based Events**: Prioritize events that offer skill development, such as coding challenges, design thinking workshops, or entrepreneurship bootcamps. These events can provide hands-on experience and practical knowledge.
> 
> 4. **Networking Opportunities**: If you are interested in building connections, prioritize events where you can interact with professionals, alumni, or industry leaders. These events can provide mentorship and open doors to future opportunities.
> 
> 5. **Registration Deadlines**: Always check the registration deadlines for events to ensure you don't miss out on opportunities. Some events may require early registration.
> 
> Since the retrieved documents do not provide event details or registration schedules, I recommend checking the official DAU website or reaching out to the Student Body Government or relevant clubs for the most up-to-date information on events and their registration schedules.

**Actual Answer (Expected)**:
> No document in this corpus ranks events by time-commitment or personal-priority fit; this requires subjective reasoning beyond the available facts.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 12606 ms
- Response Words: 281
- Similarity Score: 20.25/100
- Pass/Fail: Fail

---
### Q00088: Compare workshops, seminars, hackathons and guest lectures in terms of learning value.
**Chatbot Answer**:
> At Dhirubhai Ambani University (DAU), workshops, seminars, hackathons, and guest lectures each offer distinct learning values, tailored to different modes of engagement and educational goals. Here's a comparison based on the types of events documented in the university's records:
> 
> ---
> 
> ### **1. Workshops**
> **Learning Value:** 
> Workshops at DAU are highly interactive and hands-on, focusing on practical skill development. For example, the "Design Thinking for Innovation & Entrepreneurship Workshop" introduced participants to human-centered problem-solving techniques like empathy mapping, ideation, and prototyping. Another workshop on "Deep Learning & Artificial Intelligence: Principles & Practice" provided hands-on exposure to data-driven decision-making using tools like Power BI and R. 
> **Best For:** Students seeking to develop practical, project-based skills in specific domains like AI, design thinking, or data analytics.
> 
> ---
> 
> ### **2. Seminars**
> **Learning Value:** 
> Seminars at DAU are structured to provide in-depth knowledge and foster academic discussions. The "Silver Jubilee Seminar at DAU | ETSIF 2026" emphasized interactive evaluation, enriching participants' learning experiences through expert-led discussions and presentations. These events often feature industry experts and academics, offering insights into emerging trends and research. 
> **Best For:** Students interested in theoretical and conceptual learning, as well as networking with professionals and researchers.
> 
> ---
> 
> ### **3. Hackathons**
> **Learning Value:** 
> Hackathons are competitive, time-bound events that encourage rapid problem-solving and innovation. The "InnovAItion Hackathon 2026" involved 750+ participants from 50+ institutions, focusing on AI-based solutions to real-world challenges. Similarly, the "HackOut" event, part of DAU's Annual Techno-Cultural Fest, is a 72-hour coding competition where students build solutions to real-world problems. These events emphasize teamwork, creativity, and technical execution. 
> **Best For:** Students looking to apply their technical skills in a high-pressure, collaborative environment and gain exposure to real-world problem-solving.
> 
> ---
> 
> ### **4. Guest Lectures**
> **Learning Value:** 
> Guest lectures at DAU are typically delivered by industry experts, alumni, or distinguished academics. For instance, the "AISE 2026 – Panel Discussion" featured experts discussing the future of AI in software engineering. These events provide students with insights into industry trends, career opportunities, and emerging technologies. 
> **Best For:** Students seeking inspiration, career guidance, and exposure to industry perspectives.
> 
> ---
> 
> ### **Summary**
> | Event Type | Learning Focus | Key Features |
> |------------------|------------------------------------------|---------------------------------------------------|
> | **Workshops** | Practical, hands-on skill development | Interactive sessions, project-based learning |
> | **Seminars** | Theoretical and conceptual learning | Expert-led discussions, academic networking |
> | **Hackathons** | Innovation and problem-solving | Competitive, time-bound, team-based challenges |
> | **Guest Lectures**| Industry insights and inspiration | Career guidance, emerging trends, expert opinions |
> 
> Each event type offers unique learning opportunities, and the choice depends on your interests and goals. For example, if you're interested in AI and entrepreneurship, workshops and hackathons would provide the most direct, hands-on experience.
> 
> [Sources: 1, 2, 3, 4]

**Actual Answer (Expected)**:
> The corpus documents individual events of each type but does not itself compare categories by 'learning value' — that judgment isn't grounded in any single source.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 22782 ms
- Response Words: 451
- Similarity Score: 34.52/100
- Pass/Fail: Fail

---
### Q00089: Which event takes place immediately after orientation?
**Chatbot Answer**:
> The event that takes place immediately after the orientation program is the **commencement of classes**, which is scheduled for **27 July 2026 (tentative)**. The orientation program is set for **21-24 July 2026 (tentative)**.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Orientation program dates (e.g. 21-24 July 2026, tentative, per the NRI admissions calendar) and individual event dates exist in separate documents, but nothing in the corpus explicitly names 'the event immediately after orientation' as a cross-reference.

**Meta Data**:
- Category: event_logistics
- Latency: 5873 ms
- Response Words: 35
- Similarity Score: 52.28/100
- Pass/Fail: Pass

---
### Q00090: Which events overlap with examinations or holidays?
**Chatbot Answer**:
> Based on the academic calendar for the academic year 2026-2027, the following events overlap with examinations or holidays:
> 
> 1. **End-Semester Examination (10-07-2027 to 14-07-2027)**: This period overlaps with the Industrial Internship period, which ends on 09-07-2027.
> 
> 2. **M.Tech Major Project-1 presentation (Summer)**: This event is scheduled from 13-07-2027 to 15-07-2027, which overlaps with the End-Semester Examination period.
> 
> 3. **Announcement of Results (19-07-2027)**: This event overlaps with the commencement of the session for Autumn 2027-28.
> 
> If you need further details or have specific concerns about these overlapping events, you can visit the [DAU Academic Calendar page](https://daiict.ac.in/academic-calendar) for more information.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> No document in the corpus cross-references the events list against the exam schedule or the holiday list to flag overlaps — this would require manual cross-checking between events/ files and the Academic Calendar / Holiday List.

**Meta Data**:
- Category: event_logistics
- Latency: 9511 ms
- Response Words: 100
- Similarity Score: 38.87/100
- Pass/Fail: Fail

---
### Q00091: Has any event been cancelled or rescheduled recently?
**Chatbot Answer**:
> Based on the provided academic calendar for the Autumn 2026-27 session, there is no mention of any event being cancelled or rescheduled. All events are listed with their scheduled dates and times. 
> 
> For the **registration schedule**, the following events are highlighted:
> 
> 1. **Registration for Autumn 2026-27**: 06-07-2026 to 17-07-2026.
> 2. **Registration for Fresh PG Students**: 20-07-2026.
> 3. **Registration for Fresh BTech Students**: 31-07-2026 to 01-08-2026.
> 4. **Registration for Fresh BS-MS Students**: 03-08-2026.
> 5. **Registration for Winter 2026-27**: 07-12-2026 to 21-12-2026.
> 
> If you need further details about any specific event, please let me know!
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Only one cancellation/postponement is documented in this corpus: the Summer School on Speech Signal Processing (S4P), originally planned for July 2020, was postponed to July 2021 due to the COVID-19 pandemic — an old event, not a recent one.

**Meta Data**:
- Category: event_logistics
- Latency: 10236 ms
- Response Words: 95
- Similarity Score: 38.41/100
- Pass/Fail: Fail

---
### Q00092: Which event registrations are currently open?
**Chatbot Answer**:
> The current academic year is 2026-27, and the following event registrations are open or scheduled:
> 
> 1. **Filling of online Application Forms** is open from **24 March 2026** to **22 June 2026**.
> 2. **Fees Payment window for shortlisted candidates** is yet to be announced.
> 3. **Registration and document verification at DAU campus** is scheduled for **20 July 2026 (Tentative)**.
> 4. **Orientation Program** is scheduled for **21-24 July 2026 (Tentative)**.
> 
> For the most updated information, you can visit the official DAU website at [https://daiict.ac.in](https://daiict.ac.in).
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Registration-open status is time-sensitive and cannot be determined from this static document snapshot.

**Meta Data**:
- Category: event_logistics
- Latency: 8110 ms
- Response Words: 84
- Similarity Score: 36.51/100
- Pass/Fail: Fail

---
### Q00093: Cross-check the Events page with the Academic Calendar and identify any inconsistencies.
**Chatbot Answer**:
> After reviewing the provided academic calendar details, I did not find any inconsistencies between the events listed and the academic schedule. All events appear to be logically sequenced and aligned with the academic terms (Autumn and Summer) for the 2026-27 academic year. 
> 
> If you are referring to a specific "Registration Schedule Details" page that is not included in the current context, please provide additional information or clarify the specific inconsistency you observed. Otherwise, based on the current documents, the academic calendar appears consistent and well-organized. 
> 
> For further assistance, you can visit the [DAU Academic Calendar page](https://daiict.ac.in/academic-calendar) directly.

**Actual Answer (Expected)**:
> No pre-computed cross-check exists in the corpus; this would require comparing dates across the many individual events/ files against academics/academic_calendar.md, which is an analysis task rather than a single-document lookup.

**Meta Data**:
- Category: event_logistics
- Latency: 8508 ms
- Response Words: 97
- Similarity Score: 37.58/100
- Pass/Fail: Fail

---
### Q00094: When is Google I/O being hosted at DAU?
**Chatbot Answer**:
> I can only help with questions about Dhirubhai Ambani University — admissions, academics, faculty, research, campus life, policies, placements, and your own student records.
> 
> Ask me something about DAU and I'll do my best to help.

**Actual Answer (Expected)**:
> No mention of Google I/O being hosted at DAU appears anywhere in this corpus. This is a trap/adversarial question — DAU's Google-affiliated activity documented here is Google Developer Groups (GDG) On Campus, a student club, not the Google I/O conference.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 123 ms
- Response Words: 36
- Similarity Score: 44.39/100
- Pass/Fail: Fail

---
### Q00095: Which Nobel Prize winners are visiting DAU this semester?
**Chatbot Answer**:
> I could not find any information in the provided documents about Nobel Prize winners visiting Dhirubhai Ambani University (DAU) this semester. If you need further assistance or have additional details, please let me know. For the latest updates, you may also check the official DAU website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> No Nobel Prize winner visits are documented anywhere in this corpus. This is a trap/adversarial question — the correct response is that no such visit is recorded, not a fabricated name.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 6809 ms
- Response Words: 48
- Similarity Score: 43.74/100
- Pass/Fail: Fail

---
### Q00096: Give complete details about the next hackathon, including organizer, eligibility and deadlines.
**Chatbot Answer**:
> The next hackathon at DAU is **Code Mutants**, which is part of the **SYNAPSE’ 25** techno-cultural fest. Here are the details:
> 
> - **Organizer:** Annual Festival Committee
> - **Eligibility:** Open to students of DAU
> - **Event Dates:** Code Mutants is scheduled for **22nd Feb 2025**, from **10 AM – 11 PM**.
> - **Venue:** DAU Gandhinagar
> - **Registration Schedule and Deadlines:** Specific registration deadlines for Code Mutants are not mentioned in the provided documents. For updates on registration, you may need to check the official DAU website or contact the Annual Festival Committee directly.
> 
> For further details or to register, visit the official DAU website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> The corpus's most recent hackathon on record is HackOut'25 (organized as part of Synapse'26, DAU's annual techno-cultural festival), an August 29-31 2025, 72-hour event open to students nationally (participants came from IIT Gandhinagar, SVNIT Surat, and other institutions) via an online round followed by an offline shortlist. This is a past event in the corpus, not a forward-looking 'next hackathon' with live deadlines.

**Meta Data**:
- Category: event_logistics
- Latency: 8815 ms
- Response Words: 105
- Similarity Score: 50.20/100
- Pass/Fail: Pass

---
### Q00097: List every AI-related workshop conducted or announced by DAU.
**Chatbot Answer**:
> Based on the retrieved information, here are the AI-related workshops conducted or announced by DAU:
> 
> 1. **7 DAY AI BUILDATHON**
>  - **Organized by:** AI CLUB DAU
>  - **Email Address:** ai_club@dau.ac.in
>  - **Event Start Date:** 2026-06-13
>  - **Event End Date:** 2026-06-20
>  - **Level of Event:** Institutional
>  - **Event Report:** [Link](https://docs.google.com/document/d/1yVYh6nMEsXjwLgsvTqF3RW4iR3XNHyB4A7nHACKQW0M/edit?usp=sharing)
>  - **Excel Sheet of Participants:** [Link](https://docs.google.com/spreadsheets/d/1HZHou7tS4OTp0zMtqbzx-sMufkGJUpLMlhEW5pM89VE/edit?usp=sharing)
>  - **Google Drive with Photos:** [Link](https://drive.google.com/file/d/1d2f6b7X6KgeP3Dq3Gq2FDiiHf5V6Z_xo/view?usp=sharing)
>  - **Awards and Achievements:** [Link](https://docs.google.com/spreadsheets/d/1Ea8a_As0ZW93OtBA9IHdsaPM3TfL5XkaNMEButn8-Cg/edit?usp=sharing)
> 
> 2. **Kaggle Contest**
>  - **Organized by:** AI Club
>  - **Email Address:** ai_club@dau.ac.in
>  - **Event Start Date:** 2026-05-29
>  - **Event End Date:** 2026-05-31
>  - **Level of Event:** Institutional
>  - **Event Report:** [Link](https://docs.google.com/document/d/1VtQR7xEkg5bfRJXL17Y167iclrmvJZt0Qmfvg2JtXcE/edit?usp=sharing)
>  - **Excel Sheet of Participants:** [Link](https://docs.google.com/spreadsheets/d/1HZHou7tS4OTp0zMtqbzx-sMufkGJUpLMlhEW5pM89VE/edit?usp=sharing)
>  - **Google Drive with Photos:** [Link](https://drive.google.com/file/d/1uZpeDonrgzatv1IZbp96kw2HDQakgUSy/view?usp=sharing)
> 
> 3. **Winter School on AI-Infused Software Engineering Research and Practice (AISE)**
>  - **Event Start Date:** 07/01/2026
>  - **Event End Date:** 10/01/2026
>  - **Event Link:** [Event Details](events/6858)
> 
> 4. **One Day Interactive Workshop on Design Thinking and The Business of AI**
>  - **Event Start Date:** 03/05/2025
>  - **Event End Date:** 03/05/2025
>  - **Event Link:** [Event Details](events/6732)
> 
> These are the AI-related events that have been conducted or announced by DAU. For registration details, please check the respective links or contact the organizers directly.

**Actual Answer (Expected)**:
> Documented AI-related workshops/schools include: Workshop on AI and its Applications in VLSI Design and Technology; Workshop on Deep Learning and AI Principles & Practice (appears twice, possibly duplicate scrapes); High-End Workshop on AI/ML Algorithms and Applications in VLSI Design; One-Day Interactive Workshop on Design Thinking and the Business of AI; Three-Day Workshop on Design Thinking and AI; Two-Day School on AI and Law; Two-Day Workshop on AI Engineering Bootcamp 2026; Winter School on AI-Infused Software Engineering Research and Practice (AISE); 1st DAAIG Workshop on Modern LLMs and Applications; and the IEEE-organized InDGenius AI Summit 2025.

**Meta Data**:
- Category: event_listing
- Latency: 21949 ms
- Response Words: 189
- Similarity Score: 44.83/100
- Pass/Fail: Fail

---
### Q00098: Build a semester plan balancing academics with workshops, hackathons and club events.
**Chatbot Answer**:
> Creating a balanced semester plan requires aligning academic commitments with extracurricular opportunities like workshops, hackathons, and club events. Based on the retrieved information, here's a structured plan for the **2026-27 academic year**:
> 
> ---
> 
> ### **1. Academic Calendar Overview (2026-27)**
> - **Registration Window:** 6 July – 17 July 2026 
> - **Classes Commence (Returning + PG students):** 22 July 2026 
> - **Add-Drop Window:** 23 July – 28 July 2026 
> - **First In-Semester Examination:** 31 August – 5 September 2026 
> - **Second In-Semester Examination:** 6 October – 10 October 2026 
> - **End-Semester Examination:** 23 November – 2 December 2026 
> - **Results Announcement:** 14 December 2026 
> - **Add-Drop Window (Winter):** 5 January – 8 January 2027 
> - **B.Tech Project Presentation:** 3 – 4 May 2027 
> 
> > Note: Fresh UG students have separate registration dates. Fresh PG students typically register the Monday before classes commence.
> 
> ---
> 
> ### **2. Suggested Weekly Plan**
> To balance academics and extracurriculars, consider the following weekly structure:
> 
> #### **Weekdays (Monday–Friday)**
> - **Morning (9:00 AM – 12:00 PM):** Academic classes and study time.
> - **Afternoon (1:00 PM – 3:00 PM):** Attend workshops or club meetings (if scheduled).
> - **Evening (4:00 PM – 6:00 PM):** Hackathon preparation or club activities.
> - **Evening (6:00 PM – 8:00 PM):** Study time for upcoming exams or assignments.
> 
> #### **Weekends (Saturday–Sunday)**
> - **Saturday:** Attend major events like i.Fest (hackathons, coding competitions, robotics challenges) or club events.
> - **Sunday:** Review the week’s academic work and prepare for the upcoming week.
> 
> ---
> 
> ### **3. Key Events and Deadlines**
> - **August–September:** First In-Semester Examination period. Avoid scheduling major events during this time.
> - **October:** Second In-Semester Examination period. Plan lighter academic and extracurricular activities.
> - **November–December:** End-Semester Examination period. Focus on revision and avoid new commitments.
> - **January 2027:** Add-Drop Window and B.Tech Project Presentation. Ensure project work is prioritized during this period.
> 
> ---
> 
> ### **4. Club and Event Participation**
> DAU offers a vibrant club culture, including:
> - **Technical Clubs:** Artificial Intelligence Club, Programming Club, Microsoft Student Technical Club, Developer Students Club.
> - **Cultural Clubs:** Debate Club, Dance Club, Music Club, Theater Group.
> - **Sports Clubs:** Khelaiya Club, Concours (sports festival).
> - **Other Clubs:** Business Club, Photography and Movie Making Club, Research Club.
> 
> Participate in 1–2 clubs to manage time effectively while gaining leadership and organizational skills.
> 
> ---
> 
> ### **5. Suggested Event Participation**
> - **i.Fest (Technical Festival):** Participate in hackathons, coding competitions, and robotics challenges.
> - **Concours (Sports Festival):** Engage in team sports and leadership roles.
> - **Synapse (Cultural Festival):** Showcase talents in music, drama, dance, and debate.
> - **Club Events:** Attend club meetings and events to build skills in project management, public relations, and sponsorship.
> 
> ---
> 
> ### **6. Final Notes**
> - **Plan Ahead:** Use the academic calendar to avoid conflicts with exams and major events.
> - **Stay Flexible:** Adjust your schedule as needed based on academic workload and event schedules.
> - **Utilize Free Time:** If you have only two free hours per week, prioritize events that align with your interests and career goals (e.g., AI workshops, hackathons).
> 
> By following this plan, you can effectively balance academics with extracurricular activities and make the most of your time at DAU.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Open-ended planning task; the Academic Calendar gives the semester structure (exam windows etc.) but there's no single documented 'balanced plan' to check against.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 24899 ms
- Response Words: 521
- Similarity Score: 34.38/100
- Pass/Fail: Fail

---
### Q00099: Generate a yearly calendar of all technical, cultural and entrepreneurial events, clearly separating verified and unavailable information.
**Chatbot Answer**:
> I'll create a yearly calendar of events at Dhirubhai Ambani University (DAU) based on the information provided in the retrieved documents. I'll categorize the events into technical, cultural, and entrepreneurial categories, and clearly indicate which information is verified and which is unavailable.
> 
> ### Verified Information (from documents and)
> 
> #### Technical Events
> 1. **Winter School on AI-Infused Software Engineering Research and Practice (AISE)** 
>  - **Date:** 07/01/2026 - 10/01/2026 
>  - **Category:** Technical
> 
> 2. **Workshop on Arduino and FPGA Based Embedded System Design** 
>  - **Date:** 23/06/2025 - 27/06/2025 
>  - **Category:** Technical
> 
> 3. **Workshop on Speech and Audio Signal Processing using FPGA** 
>  - **Date:** 16/06/2025 - 20/06/2025 
>  - **Category:** Technical
> 
> 4. **One Day Interactive Workshop on Design Thinking and The Business of AI** 
>  - **Date:** 03/05/2025 
>  - **Category:** Technical
> 
> 5. **Formal Methods Update Meeting 2025** 
>  - **Date:** 03/07/2025 - 04/07/2025 
>  - **Category:** Technical
> 
> 6. **DAU to organize a Symposium on Pedagogies in Engineering Education** 
>  - **Date:** 15/11/2025 
>  - **Category:** Technical
> 
> 7. **Annual Conference of ISMMACS and the International Conference on Differential Equations** 
>  - **Date:** 07/12/2025 - 10/12/2025 
>  - **Category:** Technical
> 
> 8. **DAU to organise the 8th International Conference on Complex Dynamical Systems and Applications** 
>  - **Date:** 23/01/2026 - 26/01/2026 
>  - **Category:** Technical
> 
> #### Cultural Events
> 1. **Silver Jubilee Celebrations and Alumni Reunion: Honouring 25 Years of Excellence** 
>  - **Date:** 27/12/2025 - 28/12/2025 
>  - **Category:** Cultural
> 
> 2. **Celebrate International Yoga Day at DAU!** 
>  - **Date:** 21/06/2025 
>  - **Category:** Cultural
> 
> 3. **DAU Alumni Reconnect and Reunion** 
>  - **Date:** 03/05/2025 
>  - **Category:** Cultural
> 
> #### Entrepreneurial Events
> 1. **One Day Interactive Workshop on Design Thinking and The Business of AI** 
>  - **Date:** 03/05/2025 
>  - **Category:** Entrepreneurial
> 
> ---
> 
> ### Unavailable Information
> 
> The following information is not available in the current documents:
> - **Registration Schedule Details:** No information about registration schedules for any of the events was found in the provided documents.
> - **Event Calendar and Schedule:** While specific events are listed with dates, a comprehensive calendar format or detailed schedule is not provided in the documents.
> - **Event Overlaps with Examinations or Holidays:** The documents do not provide information about the academic calendar or holidays to determine overlaps.
> - **Event Cancellations or Rescheduling:** No information about any event cancellations or rescheduling was found in the provided documents.
> 
> ---
> 
> ### Summary
> 
> The verified information includes a list of technical, cultural, and entrepreneurial events with their dates. However, registration details, a comprehensive calendar format, information about event overlaps with academic schedules, and any cancellations or rescheduling are not available in the current documents. For the most up-to-date information, I recommend visiting the official DAU website at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> This requires synthesizing across the full events/ directory (dozens of individual event pages) plus the Academic Calendar; no single source in the corpus already provides this consolidated yearly calendar.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 26636 ms
- Response Words: 429
- Similarity Score: 29.96/100
- Pass/Fail: Fail

---
### Q00100: For every event recommendation, distinguish official DAU information from inferred recommendations.
**Chatbot Answer**:
> I'll provide information on upcoming events and distinguish between official DAU information and inferred recommendations.
> 
> ### Official DAU Events (from verified sources)
> 
> 1. **Winter School on AI-Infused Software Engineering Research and Practice (AISE)**
>  - **Date:** 7-10 January 2026
>  - **Description:** This event focuses on AI-infused software engineering research and practice.
> 
> 2. **8th International Conference on Complex Dynamical Systems**
>  - **Date:** 23-26 January 2026
>  - **Description:** An international conference focusing on complex dynamical systems.
> 
> 3. **Symposium on Pedagogies in Engineering Education**
>  - **Date:** 15 November 2025
>  - **Description:** This symposium will focus on pedagogies in engineering education.
> 
> 4. **Silver Jubilee Celebrations and Alumni Reunion**
>  - **Date:** 27-28 December 2025
>  - **Description:** Celebrating 25 years of excellence at DAU with an alumni reunion.
> 
> 5. **Annual Conference of ISMMACS and International Conference on Differential Equations**
>  - **Date:** 7-10 December 2025
>  - **Description:** A conference covering topics in mathematics and differential equations.
> 
> 6. **Commemoration of 5-year Milestone of NEP 2020**
>  - **Date:** 1 August 2025
>  - **Description:** Events focusing on Indian knowledge systems in the context of the National Education Policy.
> 
> ### Inferred Recommendations
> 
> While the following events are listed in the documents, they don't provide enough information for a complete recommendation:
> 
> 1. **Workshop on Arduino and FPGA Based Embedded System Design**
>  - **Date:** 23-27 June 2025
>  - **Recommendation:** This workshop could be valuable for students interested in embedded systems and hardware development.
> 
> 2. **Workshop on Speech and Audio Signal Processing using FPGA**
>  - **Date:** 16-20 June 2025
>  - **Recommendation:** This workshop would be beneficial for students interested in audio signal processing and FPGA technology.
> 
> 3. **One Day Interactive Workshop on Design Thinking and The Business of AI**
>  - **Date:** 3 May 2025
>  - **Recommendation:** This workshop could be valuable for students interested in design thinking and AI business applications.
> 
> 4. **DAU Alumni Reconnect and Reunion**
>  - **Date:** 3 May 2025
>  - **Recommendation:** This event would be beneficial for networking and reconnecting with DAU alumni.
> 
> ### Events with Limited Information
> 
> 1. **Formal Methods Update Meeting 2025**
>  - **Date:** 3-4 July 2025
>  - **Note:** No additional information is provided about this event.
> 
> 2. **Celebrate International Yoga Day**
>  - **Date:** 21 June 2025
>  - **Note:** No additional information is provided about this event.
> 
> For the most accurate and up-to-date information, I recommend checking the official DAU website at https://www.daiict.ac.in.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> This is an instruction about response format rather than a factual query; there is no single ground-truth 'answer' to evaluate against a source document.

**Meta Data**:
- Category: event_recommendation_reasoning
- Latency: 20261 ms
- Response Words: 385
- Similarity Score: 24.85/100
- Pass/Fail: Fail

---
### Q00101: What is the timetable for the B.Tech ICT program in Semester 3?
**Chatbot Answer**:
> The timetable for the **B.Tech. (ICT)** program in **Semester III** includes the following courses, as outlined in the retrieved documents:
> 
> ### Semester III Courses for B.Tech. (ICT) Program:
> 1. **IC-215 | HSS III (Science, Technology & Society)** 
>  - Core course 
>  - Credits: 3 
> 
> 2. **IC-216 | Object Oriented Programming** 
>  - Core course 
>  - Credits: 2 
> 
> 3. **IC-217 | Math III (Probability & Statistics)** 
>  - Core course 
>  - Credits: 4 
> 
> 4. **PC-203 | Design and Analysis of Algorithms** 
>  - Core course 
>  - Credits: 4 
> 
> 5. **PC-204 | Engineering Physics II** 
>  - Core course 
>  - Credits: 4 
> 
> 6. **PC-205 | Signal and Systems** 
>  - Core course 
>  - Credits: 4 
> 
> 7. **IC-218 | Co-curricular - 3** 
>  - Core course 
>  - Credits: 1 
> 
> 8. **IC-219 | Exploration Project** 
>  - Core course 
>  - Credits: 1 
> 
> This information is sourced from the official curriculum for the B.Tech. (ICT) program at Dhirubhai Ambani University.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> Semester 3 for ICT corresponds to the 2nd-year combined ICT/ICT-CS timetable, derived from the official Autumn 2026-27 DAU lecture timetable, filtered by course code for that branch/year.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 12443 ms
- Response Words: 149
- Similarity Score: 37.68/100
- Pass/Fail: Fail

---
### Q00102: Show me the full weekly schedule for M.Tech IT first year students.
**Chatbot Answer**:
> The retrieved documents provide information about the M.Des. (Intelligent User Experience Design) program and its course structure for Semester I. However, they do not contain the weekly schedule for M.Tech. (IT) first-year students. 
> 
> If you are looking for the M.Des. (IUxD) Semester I course structure, here is the information:
> 
> ### M.Des. (IUxD) Semester I Courses
> - **MI601 | Orientation to Intelligent User-Experience Design** (Core, Credits: 3)
> - **MI602 | Fundamentals of Design for IUxD** (Core, Credits: 5)
> - **MI603 | Elements of Design for IUxD** (Core, Credits: 4)
> - **MI604 | Intelligent Technology: An Introduction** (Core, Credits: 4)
> - **MI605 | Basics of UI, UX & IxD** (Core, Credits: 4)
> 
> For the M.Tech. (IT) program, I could not find the weekly schedule in the available university data. You may contact the academic office at **https://www.daiict.ac.in** for further assistance.

**Actual Answer (Expected)**:
> The Mtech (Core) timetable file lists the common M.Tech core-course schedule (e.g. PC512, PC503, CT505, EL467, EL411, IT457 etc.) across Tuesday-Friday, plus the shared electives grid open to all M.Tech students.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 10396 ms
- Response Words: 138
- Similarity Score: 33.17/100
- Pass/Fail: Fail

---
### Q00103: Which courses does the ICT department run on Monday mornings?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> DA-IICT does not have separate 'departments' the way the question implies — ICT is one branch among several (ICT, ICT-CS, CS-AI, ECE-AI, EVD, MNC) sharing one combined institute timetable. Monday-morning ICT-branch sessions (1st year) are drawn from the shared Institute Core courses (Intro to ICT, Calculus, Programming, Basic Electronic Circuits, Language & Literature) plus the branch-specific PC1 session at 9:00 AM in room CEP-106.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 3743 ms
- Response Words: 30
- Similarity Score: 41.16/100
- Pass/Fail: Fail

---
### Q00104: What classes are scheduled for Tuesday afternoon in the third semester of B.Tech ICT?
**Chatbot Answer**:
> The retrieved documents provide a list of courses offered in Semester III of the B.Tech. (ICT) program but do not include a detailed timetable specifying the timing of classes (e.g., Tuesday afternoon). Based on the information available:
> 
> ### Courses Offered in Semester III for B.Tech. (ICT):
> - **IC-215**: HSS III (Science, Technology & Society) (Core, Credits: 3)
> - **IC-216**: Object Oriented Programming (Core, Credits: 2)
> - **IC-217**: Math III (Probability & Statistics) (Core, Credits: 4)
> - **PC-203**: Design and Analysis of Algorithms (Core, Credits: 4)
> - **PC-204**: Engineering Physics II (Core, Credits: 4)
> - **PC-205**: Signal and Systems (Core, Credits: 4)
> - **IC-218**: Co-curricular - 3 (Core, Credits: 1)
> - **IC-219**: Exploration Project (Core, Credits: 1)
> 
> For a detailed timetable specifying class timings (e.g., Tuesday afternoon), you may need to consult the official academic calendar or the university's course schedule page at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> See the 2nd-Year (Semester 3) ICT/ICT-CS combined timetable file for the Tuesday schedule, filtered by branch/section; the source notes IT304 is used for the Computer Networks slot though the course-policy archive lists it as IT305.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 12023 ms
- Response Words: 145
- Similarity Score: 31.03/100
- Pass/Fail: Fail

---
### Q00105: Is there any class scheduled on Saturday for postgraduate students?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, there is no specific mention of classes scheduled on Saturday for postgraduate students. The document retrieved focuses on admissions and placement statistics for the M.Des. (IUxD) program and does not include details about the class schedule for postgraduate students on Saturdays. If you need further assistance, you may visit the official university website at [https://www.daiict.ac.in](https://www.daiict.ac.in) for more detailed information.

**Actual Answer (Expected)**:
> No — none of the ingested M.Tech, M.Sc. IT, M.Sc. DS, or BS-MS timetable files contain any Saturday entries; all scheduled sessions fall Monday through Friday.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 6398 ms
- Response Words: 68
- Similarity Score: 36.61/100
- Pass/Fail: Fail

---
### Q00106: What is the timetable for the M.Sc. IT program this semester?
**Chatbot Answer**:
> The M.Sc. (IT) program follows a full-time four-semester pattern. It includes three semesters of coursework followed by one semester of project work on a specified topic. Additionally, students are required to complete a four-week summer internship after the second semester and before the start of the third semester. 
> 
> However, the specific timetable for the current semester is not available in the retrieved documents. For detailed information about the current semester's timetable, I recommend visiting the official DAU website or contacting the university's academic office directly.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The M.Sc. IT Core timetable file lists that program's core-course schedule for Autumn 2026-27, derived from the official combined DAU lecture timetable.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 6891 ms
- Response Words: 87
- Similarity Score: 41.71/100
- Pass/Fail: Fail

---
### Q00107: Which subjects have back-to-back lectures on Wednesday for B.Tech?
**Chatbot Answer**:
> I could not find the specific information about subjects with back-to-back lectures on Wednesday for B.Tech in the available university data. For detailed scheduling information, I recommend visiting the official DAU website or contacting the academic office directly.

**Actual Answer (Expected)**:
> No document explicitly compiles a 'back-to-back' list; it must be derived by cross-referencing consecutive time slots (e.g. 8:00-8:50 then 9:00-9:50) within a single branch/section's timetable file — this is not something the raw data states directly.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 6070 ms
- Response Words: 38
- Similarity Score: 44.49/100
- Pass/Fail: Fail

---
### Q00108: Can you show the exam schedule for the upcoming end-semester exams?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> The Examination Department (led by the Controller of Examination) issues examination schedules and guidelines and runs an online Exam Seat Portal, but this document does not itself contain specific upcoming exam dates — those are published separately as notifications.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3706 ms
- Response Words: 30
- Similarity Score: 43.71/100
- Pass/Fail: Fail

---
### Q00109: What is the lab session schedule for the Data Structures course?
**Chatbot Answer**:
> The lab session schedule for the **Data Structures Lab using OOP (IT206)** course for the **Winter 2026** academic year is outlined in the weekly plan below:
> 
> - **Week 1 (5 Jan 2026):** Programming Paradigms, Structure of a C++ program, C++ program compilation, C++ Data types, Variables, Constants, Expressions, and Namespaces, Control Structure, Array, String. No. of Lectures: 2.
> - **Week 2 (12 Jan 2026):** C++ Function: Pass-by-value, pass-by-reference, Default arguments, Inline function, Scope, Recursion, Pointers in C++, Dynamic memory and new/delete operator; C++ Structures and Classes — Classes and Objects, Encapsulation, Class structure, Access control, static data and static function. No. of Lectures: 2.
> - **Week 3 (19 Jan 2026):** Constructors/Destructors in C++: Multiple constructor, Parametrized constructor, Copy constructor, Destructor. No. of Lectures: 1.
> - **Week 4 (26 Jan 2026):** Implementing Linked Lists using C++. No. of Lectures: 1.
> - **Week 5 (2 Feb 2026):** Inheritance: Types of inheritance, Base/derived classes, Access control & constructor order. No. of Lectures: 1.
> - **Week 6 (9 Feb 2026):** First In-Semester Examination (9 Feb Friday to 12 Feb Tuesday). No. of Lectures: —.
> - **Week 7 (16 Feb 2026):** Encapsulation and Friend Function. No. of Lectures: 1.
> - **Week 8 (23 Feb 2026):** Virtual Functions & Polymorphism: Run-time binding (late binding), Abstract class; Template: Function Template, Class Template. No. of Lectures: 1.
> - **Week 9 (2 Mar 2026):** In-Semester Break (entire week). No. of Lectures: —.
> - **Week 10 (9 Mar 2026):** Exception Handling: Try, Catch, Throw, Handling run-time errors. No. of Lectures: 1.
> 
> This schedule is specific to the **Winter 2026** academic year and is part of the **B.Tech** program.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> No course named 'Data Structures' by that exact title appears in the ingested timetable data; core/elective courses are listed by code only (e.g. IT/CS/EL series) without a code-to-title mapping in the timetable files, so this cannot be resolved from timetable data alone.

**Meta Data**:
- Category: timetable_retrieval
- Latency: 17770 ms
- Response Words: 270
- Similarity Score: 28.03/100
- Pass/Fail: Fail

---
### Q00110: Are there any timetable clashes for students taking both Machine Learning and Computer Networks this semester?
**Chatbot Answer**:
> I'm not able to retrieve that information. If you believe you should have access to this data, please contact the Academic Office.

**Actual Answer (Expected)**:
> Not answerable from the KB as posed: 'Machine Learning' does not appear as a named course in the ingested timetable data (electives are listed by code only), while 'Computer Networks' (IT304/IT305) appears in the ICT/ICT-CS 3rd-year Semester 5 timetable — there is no single document that cross-checks clashes between the two.

**Meta Data**:
- Category: adversarial_unverifiable
- Latency: 1147 ms
- Response Words: 22
- Similarity Score: 36.45/100
- Pass/Fail: Fail

---
### Q00111: Which room is the Operating Systems lecture held in?
**Chatbot Answer**:
> The retrieved documents provide detailed information about the course structure and content for two different Operating Systems courses—**IE411** and **MC214**—but **none of the documents specify the room where the lectures are held**. 
> 
> If you need further assistance, you may want to check the university's e-campus portal or contact the relevant department for the most up-to-date information on lecture room allocations.

**Actual Answer (Expected)**:
> Operating Systems (course code MC214, MNC 2nd-Year Semester 3) is held in room CEP-203, on Monday 4:00-4:50, Wednesday 12:00-12:50, and Friday 12:00-12:50.

**Meta Data**:
- Category: room_directory
- Latency: 7007 ms
- Response Words: 60
- Similarity Score: 34.90/100
- Pass/Fail: Fail

---
### Q00112: In which building is the Computer Networks lab located?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> The timetable data lists the Computer Networks lecture (IT304, ICT/ICT-CS 3rd Year Sem 5) in room LT-2/LT-3, but no separate 'Computer Networks lab' session or its building is identified in the ingested KB.

**Meta Data**:
- Category: room_directory
- Latency: 4108 ms
- Response Words: 30
- Similarity Score: 41.76/100
- Pass/Fail: Fail

---
### Q00113: What is the seating capacity of Lecture Hall 1 (LH-1)?
**Chatbot Answer**:
> The retrieved documents do not provide specific information about the seating capacity of Lecture Hall 1 (LH-1). However, they do mention the seating capacities of the Lecture Theatres (LT-1, LT-2, and LT-3) within the Lecture Complex. For example:
> 
> - **Lecture Theatre 1 (LT-1)** has a seating capacity of 390 students.
> - **Lecture Theatre 2 (LT-2)** has a seating capacity of 320 students.
> - **Lecture Theatre 3 (LT-3)** has a seating capacity of 280 students.
> 
> If you are referring to one of these lecture theatres, you can find the relevant details above. If you are specifically asking about Lecture Hall 1 (LH-1), I could not find that information in the available university data. For further assistance, you may contact the university's infrastructure or administrative office at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> DAU's Lecture Complex document names its three theatres 'LT-1', 'LT-2', and 'LT-3' (not 'LH-1') with seating capacities of 390, 320, and 280 respectively — 'LH-1' does not appear anywhere in the infrastructure data, so this is likely a naming mismatch/trap in the question.

**Meta Data**:
- Category: room_directory
- Latency: 10267 ms
- Response Words: 130
- Similarity Score: 48.98/100
- Pass/Fail: Pass

---
### Q00114: Which lecture hall is used for the introductory programming course?
**Chatbot Answer**:
> The introductory programming course, titled "Introduction to Programming," is part of the B.Tech (ICT) curriculum and is offered in Semester I. However, the retrieved documents do not specify the lecture hall or location where this course is conducted. I could not find that information in the available university data. For further assistance, you may contact the university's academic office at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> The 1st-year timetable files reference an 'Institute Core' Programming course shared across all branches, but do not specify a single fixed lecture hall for it in the ingested data (rooms vary by section/PC1 slot).

**Meta Data**:
- Category: room_directory
- Latency: 7597 ms
- Response Words: 61
- Similarity Score: 46.57/100
- Pass/Fail: Pass

---
### Q00115: Where is the Embedded Systems lab situated on campus?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> No 'Embedded Systems lab' location is named in the ingested infrastructure or timetable documents.

**Meta Data**:
- Category: room_directory
- Latency: 3846 ms
- Response Words: 30
- Similarity Score: 39.86/100
- Pass/Fail: Fail

---
### Q00116: Is there a dedicated seminar room for the ICT department?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, there is no specific mention of a dedicated seminar room for the ICT department. The documents focus on IT infrastructure and cybersecurity policies but do not detail seminar room allocations or facilities for the ICT department. If you need further assistance, you may contact the IT Department for more information.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> DAU is not organized into a separate 'ICT department' with its own seminar room in the ingested data; the Lecture Complex and CEP room series serve as shared teaching/seminar spaces across all branches.

**Meta Data**:
- Category: room_directory
- Latency: 6538 ms
- Response Words: 61
- Similarity Score: 49.11/100
- Pass/Fail: Pass

---
### Q00117: Which room hosts the B.Tech ICT Semester 5 Algorithm Design class?
**Chatbot Answer**:
> The B.Tech ICT Semester 5 Algorithm Design class is hosted in room **CEP-102** on Mondays from 8:00 to 8:50 AM, as per the Autumn 2026-27 timetable.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> 'Design and Analysis of Algorithms' appears as a course title in the ingested timetable course-name list, but the specific room for the ICT-branch Semester 5 offering is not clearly isolated in the raw data (course-code cross-referencing needed).

**Meta Data**:
- Category: room_directory
- Latency: 7176 ms
- Response Words: 28
- Similarity Score: 50.13/100
- Pass/Fail: Pass

---
### Q00118: What rooms are available for self-study or group work in the academic block?
**Chatbot Answer**:
> Based on the available information, the academic block at Dhirubhai Ambani University (DAU) provides modern facilities to support learning and innovation. Specifically, students have access to **modern laboratories, computing infrastructure, and collaborative learning spaces** that are designed to facilitate both self-study and group work. 
> 
> However, the detailed list of specific rooms or areas designated for self-study or group work is not explicitly mentioned in the current documents. For more specific details, you may want to reach out to the university's academic or infrastructure departments for the most accurate and up-to-date information.
> 
> [Sources: 3]

**Actual Answer (Expected)**:
> The Resource Centre (Library) is the primary self-study/group-work space named in the KB — spread across two Wi-Fi-enabled buildings (~16,000 sq ft) accommodating 450 users at a time; no separate 'academic block' study rooms are listed.

**Meta Data**:
- Category: room_directory
- Latency: 8292 ms
- Response Words: 93
- Similarity Score: 37.58/100
- Pass/Fail: Fail

---
### Q00119: Where is the VLSI lab on campus and how many workstations does it have?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> VLSI Design (course ED312) lectures are held in room CEP-105 per the EVD 3rd-Year timetable, but no separate 'VLSI lab' location or workstation count is given in the ingested infrastructure data.

**Meta Data**:
- Category: room_directory
- Latency: 4311 ms
- Response Words: 30
- Similarity Score: 40.98/100
- Pass/Fail: Fail

---
### Q00120: Which building houses most of the postgraduate lecture halls?
**Chatbot Answer**:
> The Lecture Complex at Dhirubhai Ambani University (DAU) houses most of the postgraduate lecture halls. This infrastructure is designed to provide a highly interactive and comfortable learning environment for students and features three air-cooled lecture theatres with varying seating capacities. The Lecture Complex is also equipped with modern audio-visual and ICT infrastructure to support hybrid learning and interactive teaching.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> PG (M.Tech/M.Sc.) core-course sessions in the ingested timetables are mostly held in CEP-series rooms (e.g. CEP-102 through CEP-212), but no document explicitly names a single 'PG building.'

**Meta Data**:
- Category: room_directory
- Latency: 6841 ms
- Response Words: 63
- Similarity Score: 38.24/100
- Pass/Fail: Fail

---
### Q00121: What time does the first lecture of the day begin for B.Tech students?
**Chatbot Answer**:
> The retrieved documents do not specify the exact timing of the first lecture for B.Tech students at Dhirubhai Ambani University. I recommend checking the official university website or contacting the academic office for detailed information on lecture timings.

**Actual Answer (Expected)**:
> The earliest scheduled slot across all ingested B.Tech timetable files is 8:00-8:50 AM.

**Meta Data**:
- Category: class_timing
- Latency: 6043 ms
- Response Words: 38
- Similarity Score: 34.48/100
- Pass/Fail: Fail

---
### Q00122: What are the timings of the lunch break for weekday classes?
**Chatbot Answer**:
> The lunch break timings for weekday classes are not explicitly mentioned in the retrieved documents. However, it is noted that weekdays are generally hectic for students due to labs and scheduled coursework, which makes it difficult for them to participate in co-curricular events. For specific lunch break timings, you may need to refer to the official university schedule or contact the university's administration for the most accurate information.
> 
> [Sources: 3]

**Actual Answer (Expected)**:
> No explicit 'lunch break' slot is stated in the ingested timetable files; there is a visible gap in most branches' schedules around midday (after the 11:00-11:50 or 12:00-12:50 slot) but it is not explicitly labeled as a lunch break.

**Meta Data**:
- Category: class_timing
- Latency: 6442 ms
- Response Words: 70
- Similarity Score: 44.22/100
- Pass/Fail: Fail

---
### Q00123: How long is a standard lecture slot at DA-IICT?
**Chatbot Answer**:
> The retrieved documents do not provide information about the standard lecture slot duration at DA-IICT. The information available pertains to specific workshops and their schedules, but no details about regular academic lecture durations are included in the provided context.

**Actual Answer (Expected)**:
> 50 minutes — every scheduled slot across the ingested timetable data runs on the hour for 50 minutes (e.g. 8:00-8:50, 9:00-9:50), with a 10-minute gap before the next slot.

**Meta Data**:
- Category: class_timing
- Latency: 5844 ms
- Response Words: 39
- Similarity Score: 37.95/100
- Pass/Fail: Fail

---
### Q00124: What time does the Probability and Statistics class start on Thursday?
**Chatbot Answer**:
> The retrieved documents do not provide specific information about the start time of the Probability and Statistics class on Thursday. The documents detail the course structure, topics covered, and lecture counts but do not include a weekly schedule with specific timings for classes. 
> 
> If you need further assistance, you can visit the university's official website at [https://www.daiict.ac.in](https://www.daiict.ac.in) or contact the academic office for more detailed information.

**Actual Answer (Expected)**:
> No course titled exactly 'Probability and Statistics' appears in the ingested data; the closest match is 'Probability and Random Processes,' whose Thursday timing (if any) would need to be looked up per-branch in the relevant timetable file.

**Meta Data**:
- Category: class_timing
- Latency: 6975 ms
- Response Words: 66
- Similarity Score: 44.94/100
- Pass/Fail: Fail

---
### Q00125: Are there any evening classes or late-afternoon sessions in the current semester?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Yes, in a limited sense — the latest slot found in the ingested timetable data is 5:00-5:50 PM (e.g. elective/M.Tech sessions); no classes are scheduled after 6:00 PM.

**Meta Data**:
- Category: class_timing
- Latency: 3463 ms
- Response Words: 30
- Similarity Score: 41.42/100
- Pass/Fail: Fail

---
### Q00126: What time does the Machine Learning lab session end on Friday?
**Chatbot Answer**:
> The Machine Learning lab session for the course **DS605: Fundamentals of Machine Learning** is scheduled on **Friday from 14:00 to 16:00 hrs**, as stated in the retrieved document. Therefore, the lab session ends at **16:00 hrs on Friday**.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> 'Machine Learning' does not appear as a named course/lab in the ingested timetable data (electives are listed by code only), so this cannot be answered from the KB as posed.

**Meta Data**:
- Category: class_timing
- Latency: 6649 ms
- Response Words: 40
- Similarity Score: 43.13/100
- Pass/Fail: Fail

---
### Q00127: When is the last lecture of the day scheduled on a typical weekday?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Based on the ingested timetable data, the latest recurring slot is 5:00-5:50 PM.

**Meta Data**:
- Category: class_timing
- Latency: 3634 ms
- Response Words: 30
- Similarity Score: 34.65/100
- Pass/Fail: Fail

---
### Q00128: What are the tutorial session timings for the Mathematics-II course?
**Chatbot Answer**:
> The Mathematics-II course, titled "Math II (Linear Algebra)" and listed with course code **IC-111**, is taught in **Semester II** and carries **4 credits**. However, the retrieved documents do not specify the tutorial session timings for this course. 
> 
> If you need further assistance, you may contact the university's academic office for detailed information on the course schedule. For more details, visit the official website: [DA-IICT Academic Curriculum](https://www.daiict.ac.in/btech-ict).
> 
> [Sources: 2, 4]

**Actual Answer (Expected)**:
> No course titled exactly 'Mathematics-II' appears in the ingested data; the closest match is 'Engineering Mathematics III' (course ED211, EVD 2nd Year), held Monday and Wednesday 12:00-12:50 and Thursday 4:00-4:50 — no session is separately labeled as a 'tutorial.'

**Meta Data**:
- Category: class_timing
- Latency: 7988 ms
- Response Words: 69
- Similarity Score: 41.04/100
- Pass/Fail: Fail

---
### Q00129: How much gap is there between back-to-back lectures in the B.Tech timetable?
**Chatbot Answer**:
> The retrieved documents do not provide specific information about the gap between back-to-back lectures in the B.Tech timetable. I could not find that information in the available university data. For further assistance, you may visit the official website at https://www.daiict.ac.in.

**Actual Answer (Expected)**:
> 10 minutes — consecutive slots run e.g. 8:00-8:50 followed by 9:00-9:50, based on the pattern seen across all ingested timetable files.

**Meta Data**:
- Category: class_timing
- Latency: 6383 ms
- Response Words: 40
- Similarity Score: 34.90/100
- Pass/Fail: Fail

---
### Q00130: At what time are the mid-semester examinations usually scheduled — morning or afternoon?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> Not specified — the Examination Department page describes its responsibilities (conducting in-semester, end-semester and special exams, seating plans, the online Exam Seat Portal) but does not state a fixed morning/afternoon slot for mid-semester exams.

**Meta Data**:
- Category: exam_structure_policy
- Latency: 3587 ms
- Response Words: 30
- Similarity Score: 41.13/100
- Pass/Fail: Fail

---
### Q00131: Who is the Head of the ICT department at DA-IICT?
**Chatbot Answer**:
> The Head of the ICT department at DA-IICT is not explicitly mentioned in the provided documents. However, the governance structure of the institute indicates that the Director leads the institute, and academic affairs are overseen by the Dean (Academic Programmes). The Dean (Research & Development) manages research and development activities. 
> 
> For specific information about the Head of the ICT department, I recommend reaching out to the Academic Office or visiting the official DA-IICT website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> DAU does not use a 'Head of Department' structure in the ingested governance data — academic leadership is organized around Deans instead (e.g. Prof. Bhaskar Chaudhury as Dean, Academic Programs, who chairs the Board of Studies ex-officio); there is no 'Head of ICT department' role in the KB.

**Meta Data**:
- Category: faculty_directory
- Latency: 7869 ms
- Response Words: 76
- Similarity Score: 48.94/100
- Pass/Fail: Pass

---
### Q00132: How many faculty members does DA-IICT currently have?
**Chatbot Answer**:
> DA-IICT currently has **no explicit mention of the total number of faculty members** in the retrieved documents. The information provided discusses the roles, responsibilities, and expectations of faculty members but does not include a specific count. 
> 
> For the most accurate and updated information, you may contact the DA-IICT administration or visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> Not stated as one number in a single document — faculty are split across five ingested categories (regular, adjunct, international adjunct, distinguished, professor of practice) each with its own set of individual profile files; a total headcount would need to be derived by counting across all five folders.

**Meta Data**:
- Category: faculty_directory
- Latency: 6660 ms
- Response Words: 56
- Similarity Score: 48.95/100
- Pass/Fail: Pass

---
### Q00133: Which faculty members hold a PhD from IIT institutes?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, the following faculty members at DA-IICT hold a PhD from IIT institutes:
> 
> 1. **Jay Prakash Lalchandani** - PhD (Computer Science), IIT Kharagpur
> 2. **Samit Bhattacharya** - PhD (Computer Science & Engineering), IIT Kharagpur
> 
> These faculty members have earned their doctoral degrees from IITs and are currently associated with DA-IICT.
> 
> [Sources: 12, 19]

**Actual Answer (Expected)**:
> Answerable only by cross-referencing each individual regular-faculty profile's 'Education' section for an IIT PhD — no single consolidated list exists in the KB.

**Meta Data**:
- Category: faculty_directory
- Latency: 7575 ms
- Response Words: 61
- Similarity Score: 40.90/100
- Pass/Fail: Fail

---
### Q00134: Who is the faculty advisor for the B.Tech ICT program?
**Chatbot Answer**:
> The retrieved documents do not provide information about the faculty advisor for the B.Tech ICT program or their biography and research details. Therefore, I could not find that information in the available university data. For further assistance, you may contact the university's administration or visit their official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> No document names a single 'faculty advisor' role for the B.Tech ICT program specifically.

**Meta Data**:
- Category: faculty_directory
- Latency: 6806 ms
- Response Words: 50
- Similarity Score: 44.83/100
- Pass/Fail: Fail

---
### Q00135: Which professor teaches the Computer Vision course at DA-IICT?
**Chatbot Answer**:
> The Computer Vision course at DA-IICT is taught by **Srimanta Mandal**, who has expertise in Image Processing, Computer Vision, and Machine Learning.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> No course explicitly named 'Computer Vision' is mapped to a specific instructor in the ingested timetable data; several regular-faculty profiles list computer vision as a research interest, but that is not the same as a confirmed current-semester teaching assignment.

**Meta Data**:
- Category: faculty_directory
- Latency: 5884 ms
- Response Words: 24
- Similarity Score: 47.33/100
- Pass/Fail: Pass

---
### Q00136: Who teaches the Theory of Computation course this semester?
**Chatbot Answer**:
> The Theory of Computation course (MC223) for the Winter 2024 semester is taught by **Puneet Bhateja**. This information is derived from the course documentation, specifically from the filename and metadata associated with the course materials.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> 'Theory of Computation' does not appear as a named course with an instructor in the ingested timetable data.

**Meta Data**:
- Category: faculty_directory
- Latency: 6404 ms
- Response Words: 38
- Similarity Score: 46.01/100
- Pass/Fail: Pass

---
### Q00137: Which faculty member is responsible for the Machine Learning course?
**Chatbot Answer**:
> The Machine Learning course at DA-IICT is associated with a group of faculty members who are involved in research and teaching in the field of AI, ML, and Data Science. The specific faculty members listed as being responsible for this area include:
> 
> - **Prof. Aditya Tatu** – Shape Modeling
> - **Prof. Anil Roy** – Assistive Technologies, Sensors and Sensing Applications, AI, ML, NLP
> - **Prof. Arpit Rana** – Applied Machine Learning, Recommendation Systems, Multimodality, and their applications in Digital Innovation and Transformation
> - **Prof. Bhaskar Chaudhury** – Computational Plasma Physics, Data Driven Plasma Engineering, Computational Electromagnetics, High Performance Scientific Computing, Computational Data Science, Applications of AI/ML
> - **Prof. Manjunath Joshi** – Computer Vision, Responsible AI, Quantum Machine Learning
> - **Prof. Prasenjit Majumder** – Natural Language Processing, Information Retrieval, Cognitive Science
> - **Prof. Pritam Anand** – Forecasting Methods, Quantile Regression, Loss Function, Support Vector Machines
> - **Prof. Rachit Chhaya** – Coresets (Provable Sampling Algorithms for ML), Fairness in ML
> - **Prof. Shruti Bhilare** – Biometrics and adversarial machine learning
> - **Prof. Sourish Dasgupta** – Natural Language Processing (Evaluation of LLMs; Personalization of LLMs; Threat Detection; Reviewer Recommendation); Knowledge Graph Inferencing (Neuro-symbolic KG Embedding & Reasoning)
> - **Prof. Srimanta Mandal** – Digital Image Processing, Computer Vision, Machine Learning
> - **Prof. Tathagata Bandyopadhyay** – Statistical Inference, Survey Sampling, Discrete Data Modeling and Analysis, Applications of Statistical Methodologies in Various Fields
> 
> These faculty members are associated with the Machine Learning course and related research areas at DA-IICT.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> 'Machine Learning' does not appear as a named, instructor-mapped course in the ingested timetable data (electives are listed by course code only).

**Meta Data**:
- Category: faculty_directory
- Latency: 14463 ms
- Response Words: 245
- Similarity Score: 39.31/100
- Pass/Fail: Fail

---
### Q00138: Who is the coordinator for the M.Tech IT program?
**Chatbot Answer**:
> The coordinator for the M.Tech IT program is not explicitly mentioned in the provided documents. Therefore, I could not find that information in the available university data. For further assistance, you may visit the official DA-IICT website at [https://www.daiict.ac.in](https://www.daiict.ac.in) or contact the administration for detailed information.

**Actual Answer (Expected)**:
> No document names a specific 'M.Tech IT program coordinator' role.

**Meta Data**:
- Category: faculty_directory
- Latency: 6637 ms
- Response Words: 46
- Similarity Score: 29.09/100
- Pass/Fail: Fail

---
### Q00139: Which professors are currently on sabbatical or leave?
**Chatbot Answer**:
> I'm not able to retrieve that information. If you believe you should have access to this data, please contact the Academic Office.

**Actual Answer (Expected)**:
> The Faculty Handbook documents the sabbatical/leave *policy* (eligibility, process), but no document lists which named faculty are currently on sabbatical or leave.

**Meta Data**:
- Category: faculty_directory
- Latency: 1446 ms
- Response Words: 22
- Similarity Score: 40.00/100
- Pass/Fail: Fail

---
### Q00140: List all assistant professors in the ICT department.
**Chatbot Answer**:
> Based on the information retrieved from the university knowledge base, the assistant professors in the ICT department at DA-IICT are as follows:
> 
> 1. **Jenson Joseph** - Assistant Professor, PhD (Communication), University of Hyderabad. Research areas include History and theory of Media, Film Studies, Cultural Studies, Malayalam Cinema, and Popular Culture.
> 2. **Manish S Chaturvedi** - Assistant Professor, PhD (ICT), DA-IICT. Research areas include Design of Intelligent Transportation Systems, Communication Protocol Design, Embedded Systems, and Internet of Things.
> 3. **Pankaj Kumar** - Assistant Professor, PhD (RF & Microwave), NIT Patna. Research areas include Bio-Inspired Metasurface/Metamaterial Devices, Terahertz Devices, Semiconductor Device Modeling and Simulation, and VLSI Design.
> 4. **Parul Gupta** - Assistant Professor, PhD (Economics), IIT Delhi. Research areas include Economic Development, Education Policy, and Economics of Gender.
> 5. **Pratim Roy** - Assistant Professor, PhD (Physics), IIT Kanpur. Research areas include Theoretical Physics, ADS/CFT Duality, and Quantum Field Theory.
> 6. **Pritam Anand** - Assistant Professor, PhD (Computer Science), South Asian University, New Delhi. Research areas include Support Vector Machines, Loss Functions, Regression, Extreme Learning Machine, and Quantile Regression.
> 7. **Prosenjit Kundu** - Assistant Professor, PhD (Mathematics), Visva-Bharati University, Shantiniketan, West Bengal. Research areas include Physics and Mathematical Sciences, Applied Mathematics, Complex Networks, and Dynamical Systems.
> 8. **Purbasha Das** - Assistant Professor, PhD (History), Jawaharlal Nehru University, New Delhi. Research areas include History of Transport and Communication, Urban History, and Legal and Social History.
> 9. **Puspendra Kumar** - Assistant Professor, PhD (Mathematics), National Institute of Technology Puducherry. Research areas include Fractional Calculus, Mathematical Modeling, Numerical Analysis, and Neural Networks.
> 10. **Rachit Chhaya** - Assistant Professor, PhD (Computer Science), IIT Gandhinagar. Research areas include Coresets for Machine Learning.
> 
> This list is based on the information provided in the retrieved document for the academic year 2024-25.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> DAU's ingested faculty data is organized by category (regular/adjunct/international adjunct/distinguished/professor of practice), not by department or specific rank like 'Assistant Professor' — a list would need to be compiled by checking each regular-faculty profile's designation field.

**Meta Data**:
- Category: faculty_directory
- Latency: 16735 ms
- Response Words: 293
- Similarity Score: 23.88/100
- Pass/Fail: Fail

---
### Q00141: Who are the faculty members who joined DA-IICT in the last five years?
**Chatbot Answer**:
> Based on the information provided in the retrieved document, the following faculty members are associated with research at DA-IICT:
> 
> 1. Anish Mathuria
> 2. Bhaskar Chaudhury
> 3. Deepak Ghodgaonkar
> 4. Maniklal Das
> 5. Manjunath V. Joshi
> 6. Mukesh Tiwari
> 7. Nabin Kumar Sahu
> 8. Rajib Lochan Das
> 9. Rutu Parekh
> 10. Saurabh Tiwari
> 11. Srimanta Mandal
> 12. Tapas Kumar Maiti
> 13. Vinay Palaparthy
> 14. Yash Vasavada
> 
> However, the document does not provide specific information about when these faculty members joined DA-IICT. Therefore, I cannot determine which of these faculty members joined in the last five years. For more detailed information, you may need to contact the university directly or refer to additional resources.

**Actual Answer (Expected)**:
> Not directly answerable — individual faculty profiles may include a joining date, but no consolidated 'recently joined' list exists in the KB.

**Meta Data**:
- Category: faculty_directory
- Latency: 9342 ms
- Response Words: 112
- Similarity Score: 35.84/100
- Pass/Fail: Fail

---
### Q00142: Which faculty member has won a teaching excellence award?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, there is no mention of any faculty member at DA-IICT who has won a teaching excellence award. Therefore, I cannot provide the requested information. If you need further assistance or have additional questions, feel free to ask.

**Actual Answer (Expected)**:
> No document in the ingested achievements or faculty data names a specific teaching-excellence-award recipient.

**Meta Data**:
- Category: faculty_directory
- Latency: 5885 ms
- Response Words: 46
- Similarity Score: 39.90/100
- Pass/Fail: Fail

---
### Q00143: Is there a dedicated faculty member for entrepreneurship and innovation?
**Chatbot Answer**:
> Yes, DA-IICT has a dedicated focus on entrepreneurship and innovation, as outlined in the Faculty Handbook and Entrepreneurship Policy. The university encourages the establishment of start-ups and mandates that each start-up must identify a faculty member from DA-IICT to mentor its operations. The role of the faculty member can vary, including being a mentor, director, or equivalent.
> 
> The university also emphasizes innovation and design, aiming to create an environment that fosters new ideas and innovative propositions. Additionally, the administrative composition of start-ups can involve faculty members in various capacities, such as promoters, mentors, consultants, or board members. 
> 
> For more detailed information, you can visit the official DA-IICT website at [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> The Faculty Entrepreneurship Policy document describes the *policy* enabling faculty to pursue entrepreneurial ventures, but does not name a specific faculty member as a dedicated entrepreneurship/innovation lead.

**Meta Data**:
- Category: faculty_directory
- Latency: 8877 ms
- Response Words: 112
- Similarity Score: 43.44/100
- Pass/Fail: Fail

---
### Q00144: Which faculty member supervises the robotics student club?
**Chatbot Answer**:
> The faculty member who supervises the **Research Club** (which appears to be the club associated with robotics and research-related activities) is **Prof. Yash Vasavada** for the academic year 2026-27. 
> 
> For the academic year 2024-25, the **Radio Club** is supervised by **Prof. Vinay Palaparthy**, but there is no mention of a dedicated robotics club in the retrieved data. 
> 
> If you are referring to the **Research Club**, the current faculty mentor is **Prof. Yash Vasavada**. For more information or direct communication, you can contact the Dean (Research) Office at **research_club@dau.ac.in** or **07968261676**.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> Student Body Government event/club records mention robotics-related student activity, but no document names a specific faculty supervisor for a robotics club.

**Meta Data**:
- Category: faculty_directory
- Latency: 9402 ms
- Response Words: 94
- Similarity Score: 40.00/100
- Pass/Fail: Fail

---
### Q00145: Who is the Dean of Academic Affairs at DA-IICT?
**Chatbot Answer**:
> The Dean of Academic Affairs at DA-IICT is **Dr. Maniklal Das**. He oversees academic excellence through research-led teaching and is responsible for faculty development and interdisciplinary education programs at undergraduate, postgraduate, and doctoral levels. The Faculty Affairs Office focuses on attracting, developing, and retaining top academic talent while supporting innovation and excellence in teaching and research activities. 
> 
> For more information or to contact the Dean of Faculty Affairs, you can reach out via **dean_faculty[at]dau[dot]ac[dot]in**.
> 
> [Sources: 1, 3]

**Actual Answer (Expected)**:
> The closest matching role in the KB is 'Dean, Academic Programs' — held by Prof. Bhaskar Chaudhury, who also chairs the Board of Studies in an ex-officio capacity; DAU does not use the exact title 'Dean of Academic Affairs.'

**Meta Data**:
- Category: faculty_directory
- Latency: 7325 ms
- Response Words: 77
- Similarity Score: 39.82/100
- Pass/Fail: Fail

---
### Q00146: What is the primary research domain of Prof. [Name]?
**Chatbot Answer**:
> The documents retrieved pertain to alumni profiles and do not provide information about the research domains, interests, or publications of any faculty member. Therefore, I could not find the requested information in the available university data. For detailed information on faculty research, you may visit the official website at [https://www.daiict.ac.in](https://www.daiict.ac.in).

**Actual Answer (Expected)**:
> This question uses a placeholder rather than a real name — cannot be resolved without a specific faculty member being named; each individual regular-faculty profile in the KB does list a research-interests section.

**Meta Data**:
- Category: faculty_directory
- Latency: 5377 ms
- Response Words: 50
- Similarity Score: 44.36/100
- Pass/Fail: Fail

---
### Q00147: Which faculty members work in the field of Natural Language Processing?
**Chatbot Answer**:
> At DA-IICT, the faculty member working in the field of Natural Language Processing (NLP) is **Prof. Sandip Modha**. His research interests include Natural Language Processing (NLP), Information Retrieval (IR), Evaluation Methodologies, and Computational Approaches to Social Media Data.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Roughly 10 regular-faculty profile files in the KB mention Natural Language Processing among their listed research interests; a specific list would need to be compiled by scanning each profile's research-interests section.

**Meta Data**:
- Category: research_domain
- Latency: 6284 ms
- Response Words: 40
- Similarity Score: 51.26/100
- Pass/Fail: Pass

---
### Q00148: Who at DA-IICT is doing research in computer vision and image processing?
**Chatbot Answer**:
> At DA-IICT, **Dr. Vivek Sharma** is associated with research in **computer vision** and related fields. He is a postdoctoral researcher and research scientist at the **MIT Media Lab**, focusing on computer vision, machine learning, and privacy. Additionally, he has worked as a Senior Research Scientist at **Sony AI (Sony Research Zürich)**, where his work includes computer vision and privacy-preserving machine learning. His academic background also includes affiliations with institutions like **Massachusetts General Hospital / Harvard Medical School**, **Karlsruhe Institute of Technology (KIT)**, and **KU Leuven / ETH Zürich**.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> About 11 regular-faculty profiles in the KB list computer vision/image processing among their research interests; no single consolidated directory names them together.

**Meta Data**:
- Category: research_domain
- Latency: 8570 ms
- Response Words: 90
- Similarity Score: 34.10/100
- Pass/Fail: Fail

---
### Q00149: Are there any faculty members specialising in cybersecurity or network security?
**Chatbot Answer**:
> Yes, there are faculty members at DA-IICT specialising in cybersecurity and network security. Here are the details:
> 
> 1. **Prof. Manik Lal Das** specialises in **Cyber Security, Privacy, Cryptography, and Algorithms**. You can find more information about him [here](https://www.daiict.ac.in/faculty/maniklal-das).
> 
> 2. **Prof. Anish Mathuria** focuses on **Security and Privacy in Computer Systems**. You can find more information about him [here](https://www.daiict.ac.in/faculty/anish-mathuria).
> 
> These faculty members are part of the Software Systems and Networking research cluster at DA-IICT. Additionally, there is a dedicated [Security Research Group](http://security.daiict.ac.in/) at the university.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Yes — a small number of faculty profiles (roughly 2-3) reference cybersecurity/network security as a research interest, though this is a comparatively less common specialization in the ingested faculty data versus e.g. ML or VLSI.

**Meta Data**:
- Category: research_domain
- Latency: 9517 ms
- Response Words: 87
- Similarity Score: 39.40/100
- Pass/Fail: Fail

---
### Q00150: Which professors are involved in research related to the Internet of Things (IoT)?
**Chatbot Answer**:
> The professors involved in research related to the Internet of Things (IoT) at DA-IICT include:
> 
> 1. **Prof. Sanjay Srivastava** - His research interests include the Internet of Things, protocol modelling and analysis, and simulation.
> 2. **Prof. Rutu Parekh** - Her research includes IoT applications in smart agriculture and environmental monitoring.
> 3. **Prof. Anish Mathuria** - He is involved in research on security and privacy infrastructure for IoT scenarios and applications.
> 4. **Prof. Manik Lal Das** - He collaborates with Prof. Anish Mathuria on the security and privacy infrastructure for IoT scenarios and applications.
> 5. **Prof. Vinay S Palaparthy** - He is working on an IoT-enabled sensor system for coal mines.
> 
> These faculty members are actively contributing to the field of IoT through various research projects and applications.
> 
> [Sources: 1, 2, 3, 4]

**Actual Answer (Expected)**:
> Around 11 regular-faculty profiles in the KB list IoT among their research interests; a named list would require scanning each profile individually.

**Meta Data**:
- Category: research_domain
- Latency: 10958 ms
- Response Words: 132
- Similarity Score: 30.58/100
- Pass/Fail: Fail

---
### Q00151: Which faculty members are working on deep learning or neural network research?
**Chatbot Answer**:
> Based on the retrieved documents, the following faculty members at Dhirubhai Ambani University (DAU) are working on deep learning or neural network research:
> 
> 1. **Prof. Abhishek Jindal** 
>  - Research Areas: Applications of reinforcement learning and deep learning in finance and cyber security, application of graph neural networks, and applications of reinforcement learning and deep learning in wireless communication.
>  - Project: Application of Deep learning and NLP to Finance.
> 
> 2. **Prof. G. Venkatesh, Prof. Shruti Bhilare, Prof. Srimanta Mandal, and Prof. Tathagata Bandyopadhyay** 
>  - These faculty members were involved in organizing and conducting a workshop on "Deep Learning and Artificial Intelligence: Principles & Practice" at DAU.
> 
> These are the faculty members currently associated with deep learning and neural network research or events at DAU.
> 
> [Sources: 1, 2, 4]

**Actual Answer (Expected)**:
> Roughly 10-11 regular-faculty profiles in the KB list deep learning/neural networks among their research interests.

**Meta Data**:
- Category: research_domain
- Latency: 10741 ms
- Response Words: 127
- Similarity Score: 29.63/100
- Pass/Fail: Fail

---
### Q00152: Who at DA-IICT researches VLSI design or embedded systems?
**Chatbot Answer**:
> At DA-IICT, the VLSI & Embedded Systems Research Group includes several faculty members who are actively researching in the fields of VLSI design and embedded systems. Here are the faculty members and their research focuses:
> 
> - **Prof. Biswajit Mishra**: Research Focus: Ultra-low power circuits, digital IC design.
> - **Prof. Rutu Parekh**: Research Focus: Micro/nano electronics, high voltage ASIC, embedded IoT.
> - **Prof. Sreeja Rajendran**: Research Focus: Fault tolerant circuits, QCA, hardware security.
> - **Prof. Sujay Kadam**: Research Focus: Control theory, robotics, computational neuroscience.
> - **Prof. Tapas Kumar Maiti**: Research Focus: Intelligent circuits & systems, robotics, cybernetics.
> - **Prof. Vinay Palaparthy**: Research Focus: Sensors, data acquisition, AI/ML, MEMS.
> - **Prof. Yash Agrawal**: Research Focus: VLSI interconnects, NoC, flexible electronics.
> 
> These faculty members are part of the VLSI & Embedded Systems Research Group, which is actively engaged in research areas such as low power processor design, ultra-low power IC design, embedded systems, IoT, MEMS, nanotechnology, AI/ML chip design, robotics, and machine learning for VLSI architectures.
> 
> [Sources: 1, 2, 3]

**Actual Answer (Expected)**:
> VLSI is one of the more common specializations in the ingested faculty data (~13 profiles reference it), with embedded systems appearing in roughly 7 profiles; individual names require checking each profile.

**Meta Data**:
- Category: research_domain
- Latency: 12715 ms
- Response Words: 167
- Similarity Score: 38.06/100
- Pass/Fail: Fail

---
### Q00153: Are there faculty members whose research focuses on bioinformatics or computational biology?
**Chatbot Answer**:
> Based on the information retrieved, there are no faculty members at DA-IICT whose research specifically focuses on bioinformatics or computational biology in the provided documents. The listed faculty members have research interests in areas such as theoretical computer science, robotics, and cybernetics, but none mention bioinformatics, computational biology, or related fields like biocomputing or computational genomics. 
> 
> If you need further assistance or want to explore other research domains, feel free to ask!

**Actual Answer (Expected)**:
> No regular-faculty profile in the ingested KB lists bioinformatics or computational biology as a research interest.

**Meta Data**:
- Category: research_domain
- Latency: 7630 ms
- Response Words: 72
- Similarity Score: 69.32/100
- Pass/Fail: Pass

---
### Q00154: Which professors have active funded research projects at DA-IICT?
**Chatbot Answer**:
> At DA-IICT, several professors have active funded research projects. The faculty members listed below are involved in research initiatives supported by national and international agencies:
> 
> - Prof. Anish Mathuria 
> - Prof. Bhaskar Chaudhury 
> - Prof. Deepak Ghodgaonkar 
> - Prof. Maniklal Das 
> - Prof. Manjunath V. Joshi 
> - Prof. Mukesh Tiwari 
> - Prof. Nabin Kumar Sahu 
> - Prof. Rajib Lochan Das 
> - Prof. Rutu Parekh 
> - Prof. Saurabh Tiwari 
> - Prof. Srimanta Mandal 
> - Prof. Tapas Kumar Maiti 
> - Prof. Vinay Palaparthy 
> - Prof. Yash Vasavada 
> 
> These faculty members lead research labs and guide students in interdisciplinary research areas. The institute emphasizes research-driven teaching and provides financial support for international conferences and professional development.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Sponsored-research detail spreadsheets exist in the administration data, but they were not fully ingested as a per-faculty active-projects directory in this KB snapshot.

**Meta Data**:
- Category: research_domain
- Latency: 9337 ms
- Response Words: 115
- Similarity Score: 33.65/100
- Pass/Fail: Fail

---
### Q00155: Who is researching Human-Computer Interaction (HCI) or UX at DA-IICT?
**Chatbot Answer**:
> I could not find specific information in the available university data about faculty members at DA-IICT who are researching Human-Computer Interaction (HCI) or UX. For more detailed information, you may want to visit the official DA-IICT website or contact the research office directly at research_officer[at]dau[dot]ac[dot]in for assistance.

**Actual Answer (Expected)**:
> Only about 1 regular-faculty profile in the ingested KB references HCI/UX as a research interest — this is one of the least-represented specializations in the data.

**Meta Data**:
- Category: research_domain
- Latency: 7111 ms
- Response Words: 47
- Similarity Score: 41.36/100
- Pass/Fail: Fail

---
### Q00156: Which faculty member has the most publications in machine learning journals?
**Chatbot Answer**:
> Based on the information provided in the retrieved documents, **Prof. Tathagata Bandyopadhyay** has the most publications in machine learning journals. Specifically, he has two publications listed in the documents:
> 
> 1. **Publication Title:** Inference on a regression model with a misclassified binary response. 
>  **Publication Venue:** Journal of Statistical Planning and Inference. 
>  **DOI:** https://doi.org/10.1016/j.jspi.2023.106121
> 
> 2. **Publication Title:** Determinants of disagreement: Learning from inflation expectations survey of households. 
>  **Publication Venue:** Journal of Forecasting. 
>  **DOI:** https://doi.org/10.1002/for.3031
> 
> These publications indicate his research contributions in the field of machine learning.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No document in the ingested KB ranks faculty by publication count; individual profiles may list selected publications but there is no comparative count.

**Meta Data**:
- Category: research_domain
- Latency: 8884 ms
- Response Words: 87
- Similarity Score: 31.36/100
- Pass/Fail: Fail

---
### Q00157: Are there any faculty members working on quantum computing research?
**Chatbot Answer**:
> Yes, there are faculty members at DA-IICT involved in quantum computing research. Specifically, **Prof. Jaideep Mulherkar** and **Prof. Gautam Datta** are working on a project titled *"Implementation Techniques of Discrete and Continuous Time Quantum Random Walks and their Applications"*, which is funded by the Government of India, Ministry of Electronics & Information Technology.
> 
> Additionally, **Prof. Gautam Datta** is associated with the course **SC463: Quantum Computation**, indicating his involvement in teaching and academic work in this area. 
> 
> If you need further details about their research or publications, I can guide you to the relevant resources.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> Only about 1 regular-faculty profile in the ingested KB lists quantum computing as a research interest — it is a rare specialization in this dataset.

**Meta Data**:
- Category: research_domain
- Latency: 8297 ms
- Response Words: 97
- Similarity Score: 50.78/100
- Pass/Fail: Pass

---
### Q00158: Who at DA-IICT collaborates with industry partners on research projects?
**Chatbot Answer**:
> At DA-IICT, collaboration with industry partners is encouraged and supported as part of the institute's commitment to meaningful research and innovation. The Dean of R&D, Prof. Manjunath V. Joshi, mentions that collaboration with leading universities and industry provides motivation for conducting impactful research. 
> 
> Additionally, the DA-IICT Centre for Entrepreneurship and Innovation (DCEI), established in 2011, supports innovation and entrepreneurship and has resulted in several incubates. DCEI is backed by DeitY, the Government of India, and the Government of Gujarat. 
> 
> While the provided document does not list specific faculty members or industry partners involved in these collaborations, it highlights the institute's focus on fostering such partnerships. For more detailed information on specific industry collaborations or faculty members involved, you may want to reach out to the Dean of R&D or the DCEI for the most current and detailed information.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> Individual faculty profiles and administration documents (e.g. consultancy policy, sponsored research details) reference industry collaboration generally, but no consolidated list of specific faculty-industry partnerships exists in the KB.

**Meta Data**:
- Category: research_domain
- Latency: 9314 ms
- Response Words: 140
- Similarity Score: 43.79/100
- Pass/Fail: Fail

---
### Q00159: Which professors are part of any national or international research consortiums?
**Chatbot Answer**:
> Based on the information retrieved from the university knowledge base, here are the professors who are part of national or international research consortiums:
> 
> 1. **Prof. Anil Roy** is involved in several sponsored research projects, including:
>  - **Development of Proof of Concept of “Optical Camera-based Smart Navigation System for Assisting Total Knee Arthroplasty”** with Gujarat Gas Ltd. through GCSRA.
>  - **Validation of “HoloLens Based Mixed Reality and Tool Tracking System for the Total Knee Arthroplasty Application”** with Arthro3D LLP, Ahmedabad.
> 
> 2. **Prof. Bhaskar Chaudhury** is engaged in:
>  - **Computational investigations of instability driven transport in low temperature magnetized plasma discharges using massively parallel 2D-3v PIC-MCC simulations**, funded by the National Supercomputing Mission, Government of India.
> 
> 3. **Prof. Nabin Kumar Sahu** is also part of the sponsored research efforts, though specific projects are not detailed in the retrieved context.
> 
> Additionally, the context highlights DA-IICT alumni and faculty involvement with global research institutions such as:
> - **Max Planck Institutes (Germany), EPFL Switzerland, ETH Zurich, Technical University of Munich (TUM), NUS Singapore, NTU Singapore**, and **Ivy League universities like MIT, Stanford, Harvard, and others**.
> 
> These affiliations indicate active participation in international research ecosystems and collaborations.
> 
> [Sources: 1, 2]

**Actual Answer (Expected)**:
> No document in the ingested KB lists faculty membership in specific national/international research consortiums.

**Meta Data**:
- Category: research_domain
- Latency: 12075 ms
- Response Words: 194
- Similarity Score: 45.39/100
- Pass/Fail: Pass

---
### Q00160: Who is doing research related to data privacy or federated learning?
**Chatbot Answer**:
> At DA-IICT, **Prof. Maniklal Das** is conducting research related to data privacy and federated learning. His publication titled *"SeFL: A Secure Privacy-Preserving Federated Learning"* was presented at the **IEEE Global Communications Conference (GLOBECOM 2024)**.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> A small number of faculty profiles (roughly 1-2) in the ingested KB reference data privacy or federated learning as a research interest.

**Meta Data**:
- Category: research_domain
- Latency: 6603 ms
- Response Words: 36
- Similarity Score: 49.22/100
- Pass/Fail: Pass

---
### Q00161: What is the official email address of the Head of Department?
**Chatbot Answer**:
> I could not find the official email address of the Head of Department in the available university data. The retrieved documents do not provide this specific information. For further assistance, you may visit the official website at [https://www.daiict.ac.in](https://www.daiict.ac.in) or contact the Dean's Office for details.

**Actual Answer (Expected)**:
> Not applicable as posed — DAU does not use a 'Head of Department' role in the ingested governance data (see Dean, Academic Programs instead); no such email exists in the KB.

**Meta Data**:
- Category: faculty_contact
- Latency: 6670 ms
- Response Words: 45
- Similarity Score: 45.98/100
- Pass/Fail: Pass

---
### Q00162: How can I contact the faculty advisor for B.Tech ICT?
**Chatbot Answer**:
> To contact the faculty advisor for the B.Tech. (ICT) program, you can reach out to the alumni office at **alumni_office@dau.ac.in** for assistance and guidance. If you are looking for a specific advisor or faculty member, providing their name or area of expertise might help in directing your inquiry more effectively.
> 
> [Sources: 1]

**Actual Answer (Expected)**:
> No document names a specific 'faculty advisor' role or contact for the B.Tech ICT program.

**Meta Data**:
- Category: faculty_contact
- Latency: 6734 ms
- Response Words: 52
- Similarity Score: 48.74/100
- Pass/Fail: Pass

---
### Q00163: What is the office number or room of Professor [Name]?
**Chatbot Answer**:
> I could not find the office number or room of Professor [Name] in the available university data. The provided documents only contain information about alumni profiles and do not include details about faculty members' office locations. For such information, you may contact the university's administrative office or visit the official website at https://www.daiict.ac.in for further assistance.

**Actual Answer (Expected)**:
> This question uses a placeholder rather than a real name — office/room numbers are not consistently populated across the ingested individual faculty profiles either way.

**Meta Data**:
- Category: faculty_contact
- Latency: 6091 ms
- Response Words: 56
- Similarity Score: 42.50/100
- Pass/Fail: Fail

---
### Q00164: What are the office hours of the faculty teaching the Algorithms course?
**Chatbot Answer**:
> I could not find that information in the available university data. For specific details about office hours for the Algorithms course, I recommend reaching out to the course coordinator or the department office for assistance. You can visit the official DA-IICT website at https://www.daiict.ac.in for more information.

**Actual Answer (Expected)**:
> No ingested faculty profile or timetable document specifies office hours; office-hours data does not appear anywhere in the KB.

**Meta Data**:
- Category: faculty_contact
- Latency: 2801 ms
- Response Words: 47
- Similarity Score: 43.52/100
- Pass/Fail: Fail

---
### Q00165: Is there a departmental phone number for the ICT office?
**Chatbot Answer**:
> Yes, there is a departmental phone number for the ICT office. The contact information provided is **079-68261574** for the Examination Department at DA-IICT/DAU, which is part of the ICT office.
> 
> [Sources: 2]

**Actual Answer (Expected)**:
> DAU is not organized into a separate 'ICT department office' with its own phone number in the ingested KB.

**Meta Data**:
- Category: faculty_contact
- Latency: 6056 ms
- Response Words: 32
- Similarity Score: 56.39/100
- Pass/Fail: Pass

---
### Q00166: How do I schedule an appointment with a professor for academic guidance?
**Chatbot Answer**:
> I don't have your academic programme details on file yet, so I can't retrieve curriculum-specific information accurately. Please sign out and sign back in once, then try your question again.

**Actual Answer (Expected)**:
> No document describes a formal appointment-scheduling process for academic guidance with individual faculty.

**Meta Data**:
- Category: faculty_contact
- Latency: 3624 ms
- Response Words: 30
- Similarity Score: 39.86/100
- Pass/Fail: Fail

---
### Q00167: What is the email format for faculty members at DA-IICT?
**Chatbot Answer**:
> The documents retrieved do not specify the email format for faculty members at DA-IICT. I could not find that information in the available university data. For such specific information, you may contact the institute's administrative office or visit the official website at https://www.daiict.ac.in for further assistance.

**Actual Answer (Expected)**:
> Based on individual faculty profiles in the KB, the pattern is firstname_lastname@dau.ac.in (e.g. abhishek_gupta@dau.ac.in).

**Meta Data**:
- Category: faculty_contact
- Latency: 6007 ms
- Response Words: 46
- Similarity Score: 34.55/100
- Pass/Fail: Fail

---
### Q00168: Who should I contact for PhD admission queries at DA-IICT?
**Chatbot Answer**:
> For Ph.D. admission queries at DA-IICT, including the application process, fees structure, and requirements, you should contact the **Admissions Office** of the university. The official Ph.D. admissions page is available at [https://www.daiict.ac.in/admission-phd](https://www.daiict.ac.in/admission-phd), where you can find detailed information on eligibility, application procedures, and deadlines.
> 
> ### Key Points from the Retrieved Information:
> 1. **Ph.D. Program Overview**: The Ph.D. program at DA-IICT is designed for students aiming for a career in academia or research. It emphasizes original contributions to knowledge in ICT, computational sciences, and related fields.
> 2. **Age Limit**: There is no age limit for applying to the Ph.D. program.
> 3. **Program Types**:
>  - **Ph.D. (Regular)**: A full-time program with potential financial assistance from the Institute or other agencies.
>  - **Ph.D. (Part-Time)**: For candidates with relevant work experience. Part-time candidates do not receive financial assistance from the Institute.
> 4. **NOC Deadline for Part-Time Candidates**: External part-time candidates must submit the No Objection Certificate (NOC) by **30 October 2026** to avoid cancellation of their admission.
> 
> For further assistance, you can visit the official Ph.D. admissions page or reach out to the Admissions Office directly. If you need help with specific details not covered in the documents, you can also contact the university's administrative support at their official website: [https://www.daiict.ac.in](https://www.daiict.ac.in).
> 
> [Sources: 1, 2, 4]

**Actual Answer (Expected)**:
> No single named PhD-admissions contact is specified in the ingested admissions data; general admissions pages exist but a dedicated PhD-query contact is not identified.

**Meta Data**:
- Category: faculty_contact
- Latency: 12500 ms
- Response Words: 211
- Similarity Score: 40.44/100
- Pass/Fail: Fail

---
### Q00169: How can I reach the placement officer or industry liaison faculty?
**Chatbot Answer**:
> To reach the placement officer or industry liaison faculty at DA-IICT, you can use the following contact details:
> 
> 1. **Mr. Souvik Sarkar** - *Head - Career Planning, Placement & Marketing* 
>  - **Email**: head_cpm[at]dau[dot]ac[dot]in 
>  - **Phone**: (+91) 079-68261609, (+91) [REDACTED_PHONE]
> 
> 2. **Anuradha Srivastava** - *Assistant Manager - Placement* 
>  - **Email**: placement_office[at]dau[dot]ac[dot]in 
>  - **Phone**: (+91) 079-68261646
> 
> These contacts are current for the academic year 2026. You may also visit the official [Placement Cell](https://www.daiict.ac.in/placements) or [Staff page](https://www.daiict.ac.in/staff) for more information.
> 
> [Sources: 1, 2, 4]

**Actual Answer (Expected)**:
> No document names a specific placement officer or industry-liaison faculty contact; placement process documents describe steps but not a named contact person.

**Meta Data**:
- Category: faculty_contact
- Latency: 10163 ms
- Response Words: 81
- Similarity Score: 39.56/100
- Pass/Fail: Fail

---
### Q00170: What is the contact information for the Research and Development cell at DA-IICT?
**Chatbot Answer**:
> The contact information for the Research and Development (R&D) Cell at DA-IICT is as follows:
> 
> - **Dean (Research):** Dr. Yash M. Vasavada | Email: dean_research[at]dau[dot]ac[dot]in 
> - **Research Officer:** Dr. Umang Patel | Email: research_officer[at]dau[dot]ac[dot]in 
> 
> For further assistance or specific queries related to research, you can also reach out to the **CEP Committee** at **cep[at]dau[dot]ac[dot]in** or call **07968261676**.
> 
> [Sources: 2, 3, 4]

**Actual Answer (Expected)**:
> No 'Research and Development cell' contact information appears in the ingested administration or research data.

**Meta Data**:
- Category: faculty_contact
- Latency: 8996 ms
- Response Words: 61
- Similarity Score: 62.96/100
- Pass/Fail: Pass

---