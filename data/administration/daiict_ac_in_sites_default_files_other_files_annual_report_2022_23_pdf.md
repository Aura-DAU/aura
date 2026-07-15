---
title: "AnnualReport 2022-23 pdf"
url: "https://daiict.ac.in/sites/default/files/other-files/Annual-Report_2022-23.pdf"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "PDF"
pdf_name: "AnnualReport 2022-23 pdf"
last_fixed: "2026-07-04"
fixes_applied: ['CRLF_ENCODING', 'GARBLED_ENCODING']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Input Text:** Raw PDF extraction from "AnnualReport 2022-23 pdf" (DA-IICT).
   - **Content:** Contains cover page info, dedication, cover page credit, table of contents, Board of Governors list, Director's Page message.
   - **Issues in Raw Text:** Repeated sections (cover page, contents, board/director page appear twice), OCR artifacts ("tropeR", "launnA", "reects", "procient", "rst", "ve", "nally"), page numbers, headers/footers, garbled formatting.
   - **Rules to Follow:**
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens.
     - Preserve all numbers, names, dates, codes exactly.
     - Convert tables if any (none obvious here, but lists can be formatted cleanly).
     - Remove repeated headers, page numbers, footers, OCR noise.
     - Fix obvious OCR typos (e.g., "reects" -> "reflects", "procient" -> "proficient", "rst" -> "first", "ve" -> "five", "nally" -> "finally", "ofine" -> "offline").
     - Do not add content.
     - Structure logically.

2.  **Identify Key Sections from Raw Text:**
   - Title: Annual Report 2022-23
   - Cover Page Info: Dates, Address, Contact, NAAC Grade, Awards, Dedication to Shri Dhirubhai Hirachand Ambani, Cover Page Credit.
   - Table of Contents
   - Board of Governors
   - Director's Page

3.  **Clean & Structure Content (Mental Draft):**
   *H1: Annual Report 2022-23*
   *H2: Cover Information*
   - Period: August 2022 – July 2023
   - Address: DA-IICT Road, Gandhinagar, Gujarat, India 382007
   - Contact: Tel.: +91 79 6826 1700 | Fax: +91 79 6826 1710 | Web: www.daiict.ac.in
   - Accreditations & Awards: NAAC Accreditation Grade ‘A+’, Recipient of Centre of Excellence Award by the Government of Gujarat
   - Dedication: Shri Dhirubhai Hirachand Ambani (28th December, 1932 – 6th July, 2002), Founder Chairman, Reliance Group & Founder Chairman, DA-IICT
   - Cover Page Credit: Student Aditya Chaturvedi composed abstract art for Fundamentals of Design 2 module (MDes course) under Prof. Binita Desai. Inspired by David Hockney's Hollywood paintings (1980s-2000s), emulating textures and colours.

   *H2: Table of Contents*
   - Board of Governors 6
   - Director’s Page 7
   - About the Institute 8
   - Academic Programs 10
   - Continuous Education Program 16
   - Placements and Internships 18
   - Seventeenth Convocation 25
   - Research and Development 27
   - Workshops, Special Lectures and Visitors 30
   - Faculty Publications 34
   - Awards and Professional Activities 56
   - Faculty and Staff Updates 65
   - Student Activities and Achievements 67
   - Resource Centre 77
   - Infrastructure 79
   - Annexures 81
     1. Management
     2. Theses, Projects and Reports
     3. Faculty
     4. Staff

   *H2: Board of Governors*
   - President: Mrs. Tina Anil Ambani (Patron Trustee, Dhirubhai Ambani Memorial Trust and Chairperson, Group CSR, Reliance Group)
   - Members:
     - Prof. Tridip Suhrud (Expert Academician, Provost – CEPT University and Director – L.D. Institute of Indology, Ahmedabad)
     - Ambassador T. S. Tirumurti (Expert, Indian Foreign Service (Retired); Former Secretary to the Government of India; Former Permanent Representative of India to the United Nations in New York)
     - Mr. Anmol Anil Ambani (Representative of DA-IICT Society, A Health, Technology and Finance enthusiast and entrepreneur; Director at Kokilaben Dhirubhai Ambani Hospital)
     - Prof. Bimal Kumar Roy (Head, PC Bose Centre for Cryptology and Security, Indian Statistical Institute, Kolkata)
     - Prof. Abhay Karandikar (Director, Indian Institute of Technology, Kanpur)
     - Prof. K.S. Dasgupta (Director, Dhirubhai Ambani Institute of Information and Communication Technology Society, Mumbai)
     - Shri Mukesh Kumar (Principal Secretary, Department of Higher & Technical Education, Government of Gujarat, Gandhinagar)
     - Shri Vijay Nehra (Secretary, Department of Science & Technology, Government of Gujarat, Gandhinagar)
     - Shri Punit Garg (Representative of DA-IICT Society, Executive Director and Chief Executive Officer, Reliance Infrastructure Limited)
     - Dr. Aloknath De (Chief Technical Officer, Samsung R&D Institute India, Bengaluru)
     - Shri Shrikant Kulkarni (Chief Business Officer, Reliance Power Limited, Mumbai)
     - Ms. Alpna J Doshi (Founder and CEO, Board Director, Stralynn Consulting Services, Inc.)
     - Shri Shrenik Vaishnav (Vice President (Finance), Torrent Power Limited, Ahmedabad)
     - Prof. Manik Lal Das (Dean (Academic Programs), Dhirubhai Ambani Institute of Information and Communication Technology, Gandhinagar)
     - Prof. Manjunath V. Joshi (Dean (Research & Development), Dhirubhai Ambani Institute of Information and Communication Technology, Gandhinagar)
   - Secretary: Mr. Siddharth Swaminarayan (Executive Registrar, DA-IICT, Gandhinagar)

   *H2: Director's Page*
   - Message by Tathagata Bandyopadhyay, Director
   - Content: Academic year 2022-23 marked the end of the pandemic. Transition from online to offline classes started in autumn semester 2022. Period remembered as transitioning from despair to hope.
   - Semiconductor industry faced chip shortage due to pandemic impact on China. Opportunity for India to become a hub. Institute introduced a unique four-year B.Tech in Electronics and VLSI Design (EVD) from Academic Year 2023-24. First two years build foundation, next two specialize in VLSI System Design and Electronics System Design.
   - Faculty producing significant research outputs in peer-reviewed journals/conferences. Ongoing projects funded by MeitY, Dept. of Space, SERB, GUJCOST, SAC-ISRO, TIHIIT Bombay, NLTM under MeitY.
   - Graduates attract top recruiters: Google, Microsoft, Sprinklr, DE Shaw, Atlassian, Qualcomm, Cadence, Morgan Stanley, Flipkart, KPMG, Barclays, Amazon, Goldman Sachs, LinkedIn, etc.
   - Recognitions: Centre of Excellence (COE) by Govt. of Gujarat, Five Star rating by GSIRF.
   - Regretfully notes demise of Mr. Soman Nair, Executive Registrar.
   - Gratitude to Governing Body, Reliance ADA Group, State and Central Governments.

4.  **Apply Rules & Refine:**
   - Check token limits per section: All sections are well under 256 tokens.
   - Fix OCR: "reects" -> reflects, "procient" -> proficient, "rst" -> first, "ve" -> five, "nally" -> finally, "ofine" -> offline, "tropeR launnA" -> removed, page numbers -> removed, duplicates -> removed.
   - Structure: H1, H2, H3 as needed. I'll use H2 for major sections, H3 for subsections if needed. The content naturally fits into H2s. I'll add H3s where appropriate to break down long lists or text, but the rules say "Each H2/H3 section must fit within ~256 tokens". I'll keep it concise.
   - Ensure exact preservation of names, dates, codes.
   - Format lists cleanly.
   - No extra text.

   Let's draft it carefully.

   Structure:
   # Annual Report 2022-23
   ## Cover Information
   ### General Details
   - Period: August 2022 – July 2023
   - Address: DA-IICT Road, Gandhinagar, Gujarat, India 382007
   - Contact: Tel.: +91 79 6826 1700 | Fax: +91 79 6826 1710 | Web: www.daiict.ac.in
   - Accreditations & Awards: NAAC Accreditation Grade ‘A+’ | Recipient of Centre of Excellence Award by the Government of Gujarat
   ### Dedication
   Shri Dhirubhai Hirachand Ambani (28th December, 1932 – 6th July, 2002)
   Founder Chairman, Reliance Group
   Founder Chairman, DA-IICT
   ### Cover Page Credit
   Our student, Aditya Chaturvedi, composed this abstract Art as part of the Fundamentals of Design 2 module of the MDes course under the guidance of Prof Binita Desai. The task was to choose the works of a famous artist and, using them, create a composition that reflects the artist's novel work. Aditya chose David Hockney (b. 1937), a well-known artist proficient in using diverse media. His paintings, inspired by the nature he observed from the top of Hollywood Hills from 1980s to 2000s reflect his masterful use of textures and colours and served as the inspiration for this artwork. This composition selected colours and textures present in Mr. Hockney's works, primarily his Hollywood paintings, attempting to emulate their overall look and feel.

   ## Table of Contents
   - Board of Governors 6
   - Director’s Page 7
   - About the Institute 8
   - Academic Programs 10
   - Continuous Education Program 16
   - Placements and Internships 18
   - Seventeenth Convocation 25
   - Research and Development 27
   - Workshops, Special Lectures and Visitors 30
   - Faculty Publications 34
   - Awards and Professional Activities 56
   - Faculty and Staff Updates 65
   - Student Activities and Achievements 67
   - Resource Centre 77
   - Infrastructure 79
   - Annexures 81
     1. Management
     2. Theses, Projects and Reports
     3. Faculty
     4. Staff

   ## Board of Governors
   ### President
   Mrs. Tina Anil Ambani
   Patron Trustee, Dhirubhai Ambani Memorial Trust and Chairperson, Group CSR, Reliance Group

   ### Members
   - Prof. Tridip Suhrud: Expert Academician, Provost – CEPT University and Director – L.D. Institute of Indology, Ahmedabad
   - Ambassador T. S. Tirumurti: Expert, Indian Foreign Service (Retired); Former Secretary to the Government of India; Former Permanent Representative of India to the United Nations in New York
   - Mr. Anmol Anil Ambani: Representative of DA-IICT Society, A Health, Technology and Finance enthusiast and entrepreneur; Director at Kokilaben Dhirubhai Ambani Hospital
   - Prof. Bimal Kumar Roy: Head, PC Bose Centre for Cryptology and Security, Indian Statistical Institute, Kolkata
   - Prof. Abhay Karandikar: Director, Indian Institute of Technology, Kanpur
   - Prof. K.S. Dasgupta: Director, Dhirubhai Ambani Institute of Information and Communication Technology Society, Mumbai
   - Shri Mukesh Kumar: Principal Secretary, Department of Higher & Technical Education, Government of Gujarat, Gandhinagar
   - Shri Vijay Nehra: Secretary, Department of Science & Technology, Government of Gujarat, Gandhinagar
   - Shri Punit Garg: Representative of DA-IICT Society, Executive Director and Chief Executive Officer, Reliance Infrastructure Limited
   - Dr. Aloknath De: Chief Technical Officer, Samsung R&D Institute India, Bengaluru
   - Shri Shrikant Kulkarni: Chief Business Officer, Reliance Power Limited, Mumbai
   - Ms. Alpna J Doshi: Founder and CEO, Board Director, Stralynn Consulting Services, Inc.
   - Shri Shrenik Vaishnav: Vice President (Finance), Torrent Power Limited, Ahmedabad
   - Prof. Manik Lal Das: Dean (Academic Programs), Dhirubhai Ambani Institute of Information and Communication Technology, Gandhin
