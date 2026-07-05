---
title: "sites/default/files/other-files/Closure-report-S4P-2025.pdf"
url: "https://www.daiict.ac.in/sites/default/files/other-files/Closure-report-S4P-2025.pdf"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "PDF"
pdf_name: "sites/default/files/other-files/Closure-report-S4P-2025.pdf"
last_fixed: "2026-07-04"
fixes_applied: ['OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Input Text:** Raw PDF extraction of a closure report for "7th Edition of ISCA Supported Summer School on Speech Signal Processing (S4P), July 05–09, 2025".
   - **Rules:**
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens (~200 words). Split if needed.
     - Preserve ALL numbers, names, dates, course codes, amounts exactly.
     - Convert garbled tables to Markdown tables.
     - Remove headers, footers, page numbers, OCR noise, control chars.
     - Fix obvious OCR typos only if 100% certain.
     - Use `[illegible]` for unreadable parts.
     - Do NOT add content.
   - **Raw Text Structure:**
     - Title/Cover info
     - 1 Message from organising chair
     - 2 About S4P 2025
     - 3 Committee (Patron, International Program Committee)
     - 4 Invited Speakers (list of names/affiliations)
     - 5 Industry Perspective Talks (list of names/affiliations)
     - 6 Organizing Committee (list of names/affiliations)
     - 7 Arrangement Committee (table-like list of volunteers)
     - Page numbers scattered (1, 2, 3, 4, 5, 6, 7)
     - Some OCR artifacts: "oe", "Saati", random symbols, line breaks in names, "4st edition" -> "4th edition", "5 Minute Ph.D. Thesis (5MPT)" vs "5 Minutes PhD Thesis Contest (5MPT)", "Dr. Premjeet Singh" vs "Premjit Singh", "Debmalaya Chakroborty" vs "Dr. Debmalya Chakrabarty", etc. I need to be careful to preserve exact names but fix obvious OCR splits/typos if certain. The prompt says "Preserve ALL numbers, names, dates, course codes, amounts exactly — never paraphrase data." and "Fix obvious OCR typos only when you are 100% certain". I'll stick closely to the text but fix line-break splits in names.

2.  **Process Section by Section:**

   *Title/Cover:*
   Closure Report
   7th Edition of ISCA Supported Summer School on Speech Signal Processing (S4P), July 05–09, 2025
   Organized by Speech Research Lab, Dhirubhai Ambani University (DAU) (formerly DA-IICT), Gandhinagar
   Website: https://sites.google.com/view/s4p2025/home
   Organizing Chair: Prof. (Dr.) Hemant A. Patil, Room No. 4103, Faculty Block-4, DAU, Gandhinagar–382 007, India
   Mail: hemant patil@dau.ac.in
   Telephone: +91-79-68261650
   Website: https://sites.google.com/site/hemantpatildaiict/
   Sponsors: Technical Co-sponsor

   *Section 1: Message from organising chair*
   Content is long. I'll split it into H3s if needed, but it's about ~200 words. I'll keep it as one H2, maybe split into "Appreciation & Theme", "Invited Experts", "Industry Talks & Sponsors", "Closing Remarks" to stay within token limits per section. Actually, the rule says "Each H2/H3 section must fit within ~256 tokens (~200 words). Split large sections with additional H3s." I'll split the message into logical H3s.
   Let's count words in the message: ~380 words. I'll split it.
   H3: Appreciation and Theme
   H3: Invited Experts and Researchers
   H3: Industry Perspective Talks and Sponsors
   H3: Closing Remarks

   *Section 2: About S4P 2025*
   ~180 words. Fits in one H2. I'll keep it as H2.

   *Section 3: Committee*
   Contains Patron and International Program Committee. I'll make H2 Committee, H3 Patron, H3 International Program Committee.

   *Section 4: Invited Speakers*
   List of names and affiliations. I'll format as a clean list or table. The raw text has them in columns. I'll convert to a Markdown table for clarity, or keep as a structured list. The rule says "Convert garbled table text into proper Markdown tables". I'll make a table: | Name | Affiliation |
   Let's extract carefully:
   Akihiko K. Sugiyama | Damascus Corporation, Japan
   Thomas Hain | University of Sheffield, UK
   Petr Motlicek | IDIAP, Switzerland
   Mathew Magimai Doss | IDIAP, Switzerland
   Nancy F. Chen | Institute for Infocomm Research (I2R), Singapore
   Yu Tsao | Academia Sinica, Taiwan
   Tatsuya Kawahara | Kyoto University
   Bayya Yegnanarayana | IIIT Hyderabad
   Hema A. Murthy | IIT Madras
   Srinivasan Umesh | IIT Madras
   Sriram Ganapathy | IISc Bengaluru
   K. Sri Rama Murty | IIT Hyderabad
   Vipul Arora | IIT Kanpur
   Anil Kumar Vuppala | IIIT Hyderabad
   Vinayak Abrol | IIIT Delhi
   Hemant A. Patil | DAU Gandhinagar

   *Section 5: Industry Perspective Talks*
   Similar format. I'll make a table.
   Sri Garimella | Amazon AGI, Bengaluru
   Sunil Kumar Kopparapu | TCS Research, Mumbai
   Nagaraj Adiga | Outcomes.ai, Bengaluru
   Debmalaya Chakroborty | Amazon AGI, Bengaluru
   Premjit Singh | Samsung R&D Institute, Bengaluru
   Nirmesh J. Shah | Sony Research, Bengaluru
   Bidisha Sharma | Uniphore, Bengaluru
   Dipesh K. Singh | Augnito, Bengaluru
   Thoshith S | Gnani.ai, Bengaluru

   *Section 6: Organizing Committee*
   List of names/affiliations. I'll make a table.
   Hemant A. Patil | DAU Gandhinagar, India
   Eng-Siong Chng | Nanyang Technological University (NTU), Singapore
   Mathew Magimai Doss | IDIAP Research Institute, Switzerland
   Hardik B. Sailor | Institute for Infocomm Research (I2R), Singapore
   Rodrigo Capobianco Guido | São Paulo State University (UNESP), Brazil

   *Section 7: Arrangement Committee*
   Table format in raw text:
   No. | Volunteers | Admin and Helpdesk Team
   1 | Ravindrakumar M. Purohit | Siddharth Swaminarayan
   2 | Priya A. Damdar | Krutika Raval
   3 | Dharmendra Vaghela | Kirit Pandya
   4 | Aniket Pandey | Divyam Mishra
   5 | Manish Manojku | [illegible/cut off] -> I'll just put what's there: Manish Manojku | [illegible]

   *Check Rules:*
   - H1 for title: `# Closure Report: 7th Edition of ISCA Supported Summer School on Speech Signal Processing (S4P), July 05–09, 2025`
   - H2 for major sections.
   - H3 for subsections.
   - Token limit per section: ~200 words. I'll ensure each H2/H3 block is concise.
   - Preserve exact data.
   - Fix OCR: "4st edition" -> "4th edition", "5 Minute Ph.D. Thesis" vs "5 Minutes PhD Thesis Contest" -> I'll keep as written but fix obvious splits. "Dr. Premjeet Singh" vs "Premjit Singh" -> I'll use the exact spelling from the list section. I'll standardize names as they appear in the dedicated lists.
   - Remove page numbers, headers, footers.
   - Output ONLY markdown.

   Let's draft carefully.

   Structure:
   # Closure Report: 7th Edition of ISCA Supported Summer School on Speech Signal Processing (S4P), July 05–09, 2025
   ## Organizing Details
   (Cover info)
   ## Message from Organising Chair
   ### Appreciation and Theme
   ### Invited Experts and Researchers
   ### Industry Perspective Talks and Sponsors
   ### Closing Remarks
   ## About S4P 2025
   ## Committee
   ### Patron
   ### International Program Committee
   ## Invited Speakers
   ## Industry Perspective Talks
   ## Organizing Committee
   ## Arrangement Committee

   I will now process the text into this structure, ensuring strict compliance.
   Word count check per section: I'll keep them tight.
   I'll fix line breaks in names.
   I'll convert the speaker/committee lists to tables as requested for garbled table text.
   I'll remove page numbers (1, 2, 3, 4, 5, 6, 7).
   I'll fix "4st" to "4th".
   I'll fix "Debmalaya Chakroborty" to "Debmalya Chakrabarty" (based on earlier mention) or keep as is? Rule 6 says preserve exactly. I'll keep exact spelling from the list but fix obvious OCR splits like "Dr. Debmalya Chakrabarty" vs "Debmalaya Chakroborty". I'll stick to the list version for consistency, but note the rule says preserve exactly. I'll just use the exact text from the list section.
   Actually, I'll just format exactly as provided, fixing only line-break artifacts.

   Let's draft. 
   Self-Correction/Refinement during thought:
   - Rule 5: "Each H2/H3 section must fit within ~256 tokens (~200 words). Split large sections with additional H3s."
   - I will split the Message section into 4 H3s as planned.
   - I will ensure tables are properly formatted.
   - I will remove all page numbers and footer artifacts.
   - I will check token counts roughly. Each section will be well under 200 words.
   - I will preserve all names exactly as they appear in their respective sections, fixing only line-break hyphens/splits.
   - "4st edition" -> "4th edition" (obvious OCR typo)
   - "5 Minute Ph.D. Thesis (5MPT)" and "5 Minutes PhD Thesis Contest (5MPT)" -> I'll keep both as they appear in different paragraphs, or unify to "5 Minutes PhD Thesis Contest (5MPT)"? I'll keep exact text.
   - I'll format the cover info under H2 `## Event Details` or similar.
   - Let's construct carefully. 
   - Check raw text for "oe", "Saati", random symbols: None found in this excerpt except maybe line breaks.
   - I will output only the markdown.
   - Proceed. 
   - Structure:
     # Closure Report: 7th Edition of ISCA Supported Summer School on Speech Signal Processing (S4P), July 05–09, 2025
     ## Event Details
     Organized by Speech Research Lab, Dhirubhai Ambani University (DAU) (formerly DA-IICT), Gandhinagar
     Website: https://sites.google.com/view/s4p2025/home
     Organizing Chair: Prof. (Dr.) Hemant A. Patil
     Address: Room No. 4103, Faculty Block-4, DAU, Gandhinagar–382 007, India
     Mail: hemant patil@dau.ac.in
     Telephone: +91-79-68261650
     Website: https://sites.google.com/site/hemantpatildaiict/
     Sponsors: Technical Co-sponsor

     ## Message from Organising Chair
     ### Appreciation and Theme
     On behalf of the Organizing Committee, we record our appreciation for the valuable contribution made by eminent world-class invited speakers, participants, international program committee, DAU faculty colleagues, staff, administration and student volunteers towards conducting the 7th edition of ISCA supported summer school with the theme ‘Automatic Speech Recognition (ASR)’ during July 05-09, 2025 at DAU Gandhinagar, India. This summer school gave a platform to interact with distinguished invited speakers, to discover novel methods and broaden our knowledge in the broad area of voice biometrics. Furthermore, to encourage young talent, the school presented the 6th edition of the 5 Minute Ph.D. Thesis (5MPT) contest with four ISCA endorsed cash prizes.

     ### Invited Experts and Researchers
     We were honored to host a remarkable lineup of experts and researchers from leading institutions worldwide. From Japan, we welcomed IEEE SP DLs by Prof. (Dr.) Akihiko K. Sugiyama (Founder, Damascus Corporation
