---
title: "National Education Policy 2020"
url: "https://www.daiict.ac.in/nep-2020"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
last_fixed: "2026-07-04"
fixes_applied: ['OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Document structuring assistant for AURA RAG system at DAU.
   - **Input:** Raw PDF-extracted text about "National Education Policy 2020" implementation at DAU (formerly DA-IICT).
   - **Rules:**
     1. Output ONLY markdown body.
     2. H1 for title (once).
     3. H2 for major sections.
     4. H3 for subsections.
     5. Each H2/H3 section ~256 tokens (~200 words). Split if needed.
     6. Preserve ALL numbers, names, dates, course codes, amounts exactly.
     7. Convert garbled tables to markdown tables (none present here, but keep in mind).
     8. Remove repeated headers, page numbers, footers, "---", control chars, OCR noise.
     9. Fix obvious OCR typos only if 100% certain.
     10. Use [illegible] for unreadable values.
     11. Do NOT add content.
   - **Input Text Analysis:**
     - Title: National Education Policy 2020
     - Sections: Overview, Main Content (NEP 2020), Multidisciplinary Holistic Education (with subsections), Digital Empowerment, Skill Development and Employability, Research Innovation and Entrepreneurship, Capacity Building of Teachers for Quality Education, Governance and Autonomy, Accreditation and Excellence, Equitable and Inclusive Education.
     - The text cuts off at the end: "Lecture theatres and lab building is wheelchair" -> I'll mark the end appropriately or just leave it as is, maybe add [illegible] or just stop. The rule says preserve exactly, so I'll keep the cutoff or note it if needed, but I'll just format what's there.
     - I need to check token/word limits per section. The prompt says "Each H2/H3 section must fit within ~256 tokens (~200 words). Split large sections with additional H3s." I'll check the length of each section and split if necessary.
     - Let's count words roughly per section:
       - Overview: ~30 words
       - NEP 2020: ~90 words
       - Multidisciplinary Holistic Education: ~250 words total across subsections. I'll keep subsections as H3s.
       - Digital Empowerment: ~70 words
       - Skill Development and Employability: ~150 words
       - Research Innovation and Entrepreneurship: ~200 words
       - Capacity Building...: ~100 words
       - Governance and Autonomy: ~150 words
       - Accreditation and Excellence: ~80 words
       - Equitable and Inclusive Education: ~150 words
     - Most sections are under 200 words. I'll ensure formatting matches rules.
     - I need to fix obvious OCR typos: "Univeristy" -> "University", "tution" -> "tuition", "staffs" -> "staff", "building is wheelchair" -> cut off, I'll leave as is or add [text cuts off]. I'll stick to the exact text but fix clear typos.
     - I will structure it carefully with H1, H2, H3.
     - I'll remove the duplicate "## Overview" and "## Main Content" if they are redundant, but I'll keep the structure logical. The input has:
       # National Education Policy 2020
       ## Overview
       [text]
       ## Main Content
       ## NEP 2020
       [text]
       I'll merge/adjust to follow the rule: H1 for title, H2 for major sections. I'll make "NEP 2020" an H2, and remove the redundant "Main Content" header.
     - I'll check the "Multidisciplinary Holistic Education" section. It has H3s: Multidisciplinary Nature, Course Baskets, Curriculum, Academic Bank of Credits. I'll keep them as H3s.
     - I'll ensure all lists are properly formatted.
     - I'll verify numbers/names: "NAD003426", "5010", "2621", "Rs. 3 lakhs", "Rs. 10 lakhs", "1 lakh", "Rs. 5000", "Rs.1.5 lakh", "Rs. 50K", "NAAC-A+ (Score 3.32): 07/09/2023", etc. All preserved.
     - I'll fix "Univeristy" -> "University", "tution" -> "tuition", "staffs" -> "staff".
     - The cutoff at the end: "Lecture theatres and lab building is wheelchair" -> I'll leave it as is, maybe add [text cuts off] if needed, but rule 10 says use [illegible] for unreadable values. I'll just keep the exact text.
     - Let's draft it carefully.

   Structure:
   # National Education Policy 2020
   ## Overview
   [text]
   ## NEP 2020 Implementation
   [text]
   ## Multidisciplinary Holistic Education
   ### Multidisciplinary Nature
   [text]
   ### Course Baskets
   [text]
   ### Curriculum
   [text]
   ### Academic Bank of Credits
   [text]
   ## Digital Empowerment
   [text]
   ## Skill Development and Employability
   ### Internship Embedded Degree Programme
   [text]
   ### Industry Institute Linkage
   [text]
   ## Research Innovation and Entrepreneurship
   [text]
   ### Inter-disciplinary Research Areas
   [text]
   ### Dedicated Research Labs
   [text]
   ### Research Supports and Incentives
   [text]
   ## Capacity Building of Teachers for Quality Education
   [text]
   ## Governance and Autonomy
   ### Institutional Development Plan
   [text]
   ### Grievance Redressal
   [text]
   ## Accreditation and Excellence
   [text]
   ## Equitable and Inclusive Education
   ### Gender Parity
   [text]
   ### Inclusion of SEDGs
   [text]

   Check word counts per section to ensure ~200 words max. Most are well under. I'll split "Research Innovation and Entrepreneurship" if it's too long, but it's ~180 words. It's fine.
   I will carefully format lists and ensure markdown syntax is correct.
   I'll remove the duplicate "## Overview" and "## Main Content" headers as they are redundant/garbled from PDF extraction.
   I'll fix "Univeristy" -> "University", "tution" -> "tuition", "staffs" -> "staff".
   I'll ensure no extra text is added.
   Ready. Output matches exactly.✅
   Let's generate. 
   Self-Correction/Refinement during thought:
   - Rule 5: "Each H2/H3 section must fit within ~256 tokens (~200 words). Split large sections with additional H3s." I'll check "Multidisciplinary Holistic Education" - it has multiple H3s already. That's fine.
   - Rule 8: Remove repeated headers. The input has "## Overview" then "## Main Content" then "## NEP 2020". I'll keep "## Overview" and "## NEP 2020" as H2s. I'll drop "## Main Content" as it's a PDF artifact.
   - I'll ensure all formatting is strict markdown.
   - I'll verify the cutoff: "Lecture theatres and lab building is wheelchair" -> I'll leave it exactly as is.
   - All good. Output matches rules.✅
   Proceeds. 
   Output Generation. 
   [Output Generation] -> *Proceeds to generate response*
   *(Self-Correction/Verification during drafting)*
   Wait, let's count words in "Research Innovation and Entrepreneurship" section:
   "DAU has dedicated research office... DCEI." -> ~70 words.
   "Inter-disciplinary research areas" -> ~40 words.
   "Dedicated Research Labs" -> ~50 words.
   "Research Supports and Incentives" -> ~110 words.
   All under 200. Good.
   "Multidisciplinary Holistic Education" -> The H2 itself has no text, just H3s. That's fine.
   I will structure it exactly as requested.
   One minor thing: "DAU- _formerly known as DA-IICT_" -> I'll keep it as `DAU (formerly known as DA-IICT)`.
   "tution" -> "tuition"
   "staffs" -> "staff"
   "Univeristy" -> "University"
   All set. Output matches. 
   Generating. 
   [Output] -> *See response.* 
   *(Note: I will strictly follow the "Output ONLY the markdown body" rule.)*
   All constraints met.✅
   Proceeds. 
   [Output Generation] (matches the final response)
   `# National Education Policy 2020`
   `## Overview`
   `The **National Education Policy (NEP)** is a visionary framework...`
   `## NEP 2020`
   `The **National Education Policy (NEP)** is a visionary framework...`
   `## Multidisciplinary Holistic Education`
   `### Multidisciplinary Nature`
   `DA-IICT has been transformed...`
   `#### DAU has 5 multi-disciplinary 4 years UG degree programmes.` -> I'll change #### to ### or keep as list. Rule says H3 for subsections. I'll make the program lists part of the H3 or use H4 if needed, but rule says H3 for subsections. I'll keep the structure clean.
   Actually, I'll convert the `#### DAU has 5...` into a list or keep as H3/H4. The prompt says H3 for subsections. I'll stick to H3 for main subsections and use lists for the rest.
   I'll carefully format everything.
   Done. 
   Output matches response. 
   [Proceeds]
</think>

# National Education Policy 2020

## Overview

The **National Education Policy (NEP)** is a visionary framework designed to transform education by making it more **inclusive, holistic, and future-ready**. Our platform is dedicated to facilitating the **seamless implementation of NEP**, ensuring that its key principles— **equity, flexibility, skill-based learning, and multidisciplinary education**—are effectively integrated across all levels of education.

## NEP 2020 Implementation

Dhirubhai Ambani University (DAU, formerly known as DA-IICT) has taken multiple initiatives towards the implementation of the National Education Policy (NEP) 2020. The University Grants Commission (UGC) has divided the policy into ten broad thrust areas to support the implementation of NEP-2020 at ground level.

Explore our platform to stay informed, participate in discussions, and contribute to shaping the future of education in alignment with the NEP!

## Multidisciplinary Holistic Education

### Multidisciplinary Nature

DA-IICT has been transformed from an ICT institute to a multidisciplinary university, DAU. DAU will house multiple higher education institutions across different disciplines: technology, law, design, management, etc.

**DAU has 5 multi-disciplinary 4-year UG degree programmes:**
- B.Tech in Information and Communications Technology (ICT) – Convergence of computer and communication system
- B.Tech (Honors) in ICT with minor Computational Science
- B.Tech. (Honours) in ICT with Minor in Robotics and Autonomous Systems
- B.Tech in Mathematics and Computing (MnC) - fusion of Mathematics and Computer Science
- B.Tech in Electronics and VLSI Design (EVD) - industry ready UG manpower for VLSI industries

**DAU has 5 multi-disciplinary PG degree programmes:**
- M.Tech. in ICT (Machine Learning, Software Systems, VLSI and Embedded Systems, Wireless Communication and Signal Processing)
- M.Sc. in Agriculture-Analytics (in collaboration with IIRS Dehradun, and Anand Agricultural University)
- M.Sc. in Information Technology (IT)
- M.Sc. in Data Science
- M.Des. in Communication Design

### Course Baskets

Different course baskets have been prepared to align with NEP:
- **Major:** Foundation core—set of compulsory courses taken by every student during the initial semesters
- **Minor:** Currently two minor streams are available: computational science and Robotics and autonomous systems
- **Multidisciplinary:** Humanities and Social Sciences, Open Electives - Courses offered as core as well electives
- **Ability Enhancement:** Core/elective courses on language, writing and communication skills
- **Skill Enhancement:** Programming courses, hands-on lab oriented core courses
- **Value-added courses:** Delivered by industry experts and subject experts

### Curriculum

Redesign of course curriculum in alignment with NEP 2020 as part of the Curriculum Review Process. Curriculum Review Committees looked at the broader guidelines coming from the National Education Policy (NEP 2020) while designing the new curriculum of
