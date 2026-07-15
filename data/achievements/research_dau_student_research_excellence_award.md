---
title: "Research / DAU Student Research Excellence Award"
url: "https://www.daiict.ac.in/dau-student-research-excellence-award"
category: "Achievements"
scraped_by: "Dhruvam"
scraped_date: "2026-06-01"
team: "Team 2"
last_fixed: "2026-07-04"
fixes_applied: ['CRLF_ENCODING', 'OCR_NOISE']
---

<think>
Here's a thinking process:

1.  **Analyze User Input:**
   - **Role:** Document structuring assistant for AURA RAG system at DAU.
   - **Input:** Raw PDF-extracted text about "DAU Student Research Excellence Award".
   - **Rules:**
     - Output ONLY markdown body.
     - H1 for title.
     - H2 for major sections.
     - H3 for subsections.
     - Keep sections ~256 tokens (~200 words). Split if needed.
     - Preserve ALL numbers, names, dates, course codes, amounts exactly.
     - Convert garbled table text into proper Markdown tables.
     - Remove repeated headers, page numbers, footers, "---", control chars, OCR noise.
     - Fix obvious OCR typos only if 100% certain.
     - Use `[illegible]` for unreadable values.
     - Do NOT add content.
   - **Raw Text Analysis:**
     - Title: Research / DAU Student Research Excellence Award
     - Sections: Overview, Main Content (Policy, Award, Eligibility Criteria, Selection Criteria and Process, List of Awardees), Award, Eligibility Criteria, Selection Criteria and Process, UG Programs, PG Programs, Ph.D. Program (repeated), Tables (garbled CSV-like format).
     - The table data is messy, with repeated headers and missing student names in some rows. I need to reconstruct it carefully into a proper Markdown table.
     - I'll structure it logically: H1 Title, H2 Overview, H2 Award, H2 Eligibility Criteria, H2 Selection Criteria and Process, H2 List of Awardees (with subsections for UG, PG, PhD if possible, or just one table split logically).
     - The raw text has repeated "UG Programs", "PG Programs", "Ph.D. Program" headings before the table. I'll use these as H3s under "List of Awardees".
     - The table data needs careful parsing. I'll extract columns: NAME OF THE STUDENT, STUDENT ID, PUBLICATION MONTH, PUBLICATION VENUE, DAU FACULTY AUTHORS, TITLE, DOI.
     - I'll clean up the table rows, fixing missing names where obvious, or leaving them as is if unclear. I'll ensure proper markdown table formatting.
     - I'll split the large table into subsections if it exceeds ~200 words, or just keep it as one table but ensure the overall section length is managed. Actually, tables count towards tokens. I'll split the awardees list into UG, PG, PhD based on the context or just present the cleaned table under H2 List of Awardees, and maybe split it into H3s if needed. The raw text has "UG Programs", "PG Programs", "Ph.D. Program" repeated. I'll use them as H3s.
     - Let's parse the table data carefully.

     Table parsing:
     Headers: | NAME OF THE STUDENT | STUDENT ID | PUBLICATION MONTH | PUBLICATION VENUE | DAU FACULTY AUTHORS | TITLE | DOI |
     Row 1: CHAITANYA MEHUL SHETH | 202101030 | Jul-25 | IEEE Sensors Journal | MANISH KUMAR | UASPAR: Utility-based Adaptive Sensor Placement and Reconfiguration for Energy Efficient Wireless Sensor Networks | 10.1109/JSEN.2025.3590153
     Row 2: DEVANSH PATEL | 202001262 | Apr-25 | Association For The Advancement Of Artificial Intelligence (AAAI) | SOURISH DASGUPTA, ANIL K. ROY | Are Key-Phrases All That Reviewers Care About? A Comprehensive Benchmarking of Reviewer Matchmaking Systems | https://doi.org/10.1609/aaai.v39i22.34545
     Row 3: DHRUV PRAJAPATI | 202001103 | Dec-25 | IEEE Transactions On Vehicular Technology | MANISH KUMAR | URCR: UAV-Aided Reputation-Based Cluster Routing in Vehicular Ad Hoc Networks | 10.1109/TVT.2025.3645994
     Row 4: GANGARAJU BOPPARAM | 202001107 | Dec-25 | IEEE Transactions On Vehicular Technology | MANISH KUMAR | URCR: UAV-Aided Reputation-Based Cluster Routing in Vehicular Ad Hoc Networks | 10.1109/TVT.2025.3645994
     Row 5: KANDARP DEVMURARI | 202001052 | Jul-25 | IEEE Sensors Journal | MANISH KUMAR | UASPAR: Utility-based Adaptive Sensor Placement and Reconfiguration for Energy Efficient Wireless Sensor Networks | 10.1109/JSEN.2025.3590153
     Row 6: PRAJAPATI NATVAR MOHANBHAI | 202101402 | Oct-25 | IEEE Communications Letters | MANISH KUMAR | An Efficient Hybrid Cooperative Target Search for UAV Swarms | 10.1109/LCOMM.2025.3617976
     Row 7: PRARTHEE BHAVINBHAI DESAI | 202001257 | Apr-25 | Association For The Advancement Of Artificial Intelligence (AAAI) | SOURISH DASGUPTA ANIL K. ROY | Are Key-Phrases All That Reviewers Care About? A Comprehensive Benchmarking of Reviewer Matchmaking Systems | 10.1609/aaai.v39i22.34545
     Row 8: SHASHANK UPADHYAY | 202101411 | Oct-25 | IEEE Communication Letters | MANISH KUMAR | An Efficient Hybrid Cooperative Target Search for UAV Swarms | 10.1109/LCOMM.2025.3617976
     Row 9: VIHAR SHAH | 202001110 | Mar-25 | IEEE ANTS 2024 | MANISH KUMAR, ABHUSHEK JINDAL | An Energy Efficient UAV Path Planning for Data Collection in Multi-Node IoT System | 10.1109/ANTS63515.2024.10898404
     Row 10: HIYA CHAUDHARI | 202101047 | Dec-25 | EUSIPCO 2025 | Hemant A. Patil | ANALYSIS AND CLASSIFICATION OF NORMAL VS. PATHOLOGICAL INFANT CRIES | 10.23919/EUSIPCO63237.2025.11226653
     (Header repeats)
     Row 11: ADARSH GUPTA | 202411083 | Jul-25 | IEEE Sensors Applications Symposium (SAS) 2025 | YASH AGARWAL, SREEJA RAJENDRAN, VINAY S PALAPARTHY | In-Situ Benchmarking of Oxide-Based Leaf Wetness Sensor for Integrated Plant Disease Management | 10.1109/SAS65169.2025.11105121
     Row 12: [Missing Name] | [Missing ID] | Jul-25 | IEEE Sensors Applications Symposium (SAS) 2025 | MANJUNATH V JOSHI, AHLAD KUMAR, VINAY S PALAPARTHY | Multi-Sensor System for Optimum Irrigation and Plant Disease Detection Using Multilayer Perceptron Model on Mango Plant | 10.1109/SAS65169.2025.11105132
     Row 13: ATUL MAKWANA | 202411051 | Dec-25 | IEEE ANTS 2025 | MANIK LAL DAS | An Improved Verifiable Database at Page-Level Tampering Detection | https://ants2025.ieee-ants.org/program/accepted-papers
     Row 14: DAKSH ARVINDBHAI PATEL | 202411091 | Dec-25 | PReMI 2025 | HEMANT A. PATIL | Audio Deepfake Detection using Fusion of Fractal and MFCCs Features | https://premi25.iitd.ac.in/Papers/List%20of%20Accepted%20Papers%20of%20PReMI%202025.pdf
     Row 15: DHAIRYA MARADIYA | 202211043 | Dec-25 | CODS-COMAD | ABHISHEK JINDAL, CYRIL JOS | Integrating price and textual data for next-day stock movement prediction: A study using StockNet dataset | https://doi.org/10.1007/s44248-025-00076-w
     Row 16: KAUSTUBH WADE | 202418024 | Dec-25 | PReMI 2025 | HEMANT A. PATIL | LaghuVani: How Clearly Can Tiny Vocoders Speak Bengali and Maithili? | https://premi25.iitd.ac.in/Papers/List%20of%20Accepted%20Papers%20of%20PReMI%202025.pdf
     Row 17: KRISHNA VEER SINGH | 202211048 | Jul-25 | International Joint Conference on Neural Networks (IJCNN) | MANJUNATH V. JOSHI | Super-Resolution Using Dual-Stage Generative Adversarial Network (DS-GAN) and IGMRF Prior | 10.1109/IJCNN64981.2025.11227240
     Row 18: NIRMAL DIPAKKUMAR SHAH | 202311043 | Aug-25 | Plasma Physics And Controlled Fusion | BHASKAR CHAUDHURY | Efficient SVD-based approach for extracting plasma-relevant features from tokamak imaging diagnostics | 10.1088/1361-6587/adf99a
     Row 19: SAROJ PANDIT | 202418048 | Dec-25 | PReMI 2025 | HEMANT A. PATIL | Whisper-Based Multilingual ASR for Indic Languages | https://premi25.iitd.ac.in/Papers/List%20of%20Accepted%20Papers%20of%20PReMI%202025.pdf
     (Header repeats)
     Row 20: AARUSHI DHAMI | 201921008 | Mar-25 | National Conference On Communication 2025 | YASH VASAVADA | A Low-Complexity Blind Iterative Projections Approach for Beamforming and Channel Estimation | 10.1109/NCC63735.2025.10983243
     Row 21: AVINASH D PAWAR | 202421032 | Jul-25 | IEEE Sensors Journal | VINAY S. PALAPARTHY | Detection of Small Water Droplets on Flexible Leaf Wetness Sensor Considering Effect of Spatiotemporal Variation | 10.1109/JSEN.2025.3585731
     Row 22: [Missing Name] | [Missing ID] | Jul-25 | IEEE Sensors Applications Symposium (SAS) 2025 | VINAY S. PALAPARTHY, YASH AGARWAL, SREEJA RAJENDRA | Effect of Field Contaminants on rGO-coated Flexible Leaf Wetness Sensors for In-Situ Agriculture Applications | 10.1109/SAS65169.2025.11105124
     Row 23: [Missing Name] | [Missing ID] | Jul-25 | IEEE Sensors Applications Symposium (SAS) 2025 | VINAY S. PALAPARTHY, YASH AGARWAL, SREEJA RAJENDRA | In-Situ Benchmarking of Oxide-Based Leaf Wetness Sensor for Integrated Plant Disease Management | 10.1109/SAS65169.2025.11105121
     Row 24: [Missing Name] | [Missing ID] | Jul-25 | IEEE Sensors Applications Symposium (SAS) 2025 | VINAY S PALAPARTHY, SREEJA RAJENDRAN, YASH AGARWAL | IoT Enabled Sensor Interface Circuit for rGO/SnO2 Nanocomposite based Leaf Wetness Sensors | 10.1109
