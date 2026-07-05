---
title: "N.I.R.F. / Top Universities/Institute Admission Data/Details of No. of Graduating students admitted into Top University/Institute. (11.5 KB)"
url: "https://www.daiict.ac.in/sites/default/files/TopUniversityDetails_3D-1.xls"
category: "administration"
scraped_by: "Om Patel"
scraped_date: "2026-05-31"
team: "Team E"
source_type: "Excel"
pdf_name: "N.I.R.F. / Top Universities/Institute Admission Data/Details of No. of Graduating students admitted into Top University/Institute. (11.5 KB)"
last_fixed: "2026-07-04"
fixes_applied: ['EXCEL_BAD_HEADERS', 'CHUNK_OVERFLOW']
---

### Initial Analysis and Verification
Here's a thinking process:

1.  **Analyze User Input:**
    -   **Input Table:** A markdown table with headers: `| S.No. | Name of the student of your institution | Graduating year of the student | PG/PhD program in where student has been admitted | Name of the top university/institutions | Year of admission |`
    -   **Problem Statement:** The prompt says "fix the Unnamed: N headers", but the provided table *already* has proper headers. Wait, let me check carefully. The prompt says "BROKEN MARKDOWN TABLE (fix the Unnamed: N headers):" but the table provided actually has correct headers. This might be a template prompt where the user pasted a table that already looks fixed, or maybe the "Unnamed" part was in the original Excel but got cleaned up before pasting? Or maybe I just need to output the table exactly as is, ensuring it's properly formatted markdown.
    -   Let's verify the table structure. It has 6 columns. The headers are descriptive. The data rows match. There are some empty rows and note rows at the bottom that span multiple columns or are just notes.
    -   The prompt says: "Output ONLY the fixed markdown table(s) — no preamble or explanation."
    -   I will just output the table exactly as provided, ensuring it's valid markdown. Since it already looks correct, I'll just reproduce it cleanly. If there were "Unnamed: 0" headers, I'd replace them, but there aren't any. I'll assume the user wants the table formatted correctly as markdown.
    -   Wait, let's look at the bottom rows:
        `| Note: Please enter data for students who have graduated in year 2015-16 from your institute and got admitted in PG/PhD program of a top institution |  |  |  |  |  |`
        `| 2. Institutions ranked as top institutions in the following ranking bodies namely India Ranking 2016, QS World Ranking 2016, THE World University Ranking 2016. |  |  |  |  |  |`
        These are notes that got merged into the first column. I should keep them as is, or maybe format them properly. The prompt says "Preserve all data values exactly."

### Double-Checking the Exact Input Table
Let's double-check the exact input table:

```markdown
| S.No. | Name of the student of your institution | Graduating year of the student | PG/PhD program in where student has been admitted | Name of the top university/institutions | Year of admission |
| --- | --- | --- | --- | --- | --- |
| 1 | BHUTIYA SIDDHARTH RAMBHAI | 2015-16 | PG | University of Southern California | 2016 |
...
| 20 | SONI SAPAN | 2015-16 | PG | University of Toronto | 2017 |
|  |  |  |  |  |  |
| Note: Please enter data for students who have graduated in year 2015-16 from your institute and got admitted in PG/PhD program of a top institution |  |  |  |  |  |
| 2. Institutions ranked as top institutions in the following ranking bodies namely India Ranking 2016, QS World Ranking 2016, THE World University Ranking 2016. |  |  |  |  |  |
```

### Minor Adjustments and Final Check
It's already well-formed. I will just output it exactly as requested. No extra text.
One minor thing: The prompt says "fix the Unnamed: N headers", but the provided table doesn't have them. This is likely a copy-paste artifact from the user's workflow. I will just output the table as is, ensuring it's valid markdown.

### Output Generation
```markdown
| S.No. | Name of the student of your institution | Graduating year of the student | PG/PhD program in where student has been admitted | Name of the top university/institutions | Year of admission |
|---|---|---|---|---|---|
| 1 | BHUTIYA SIDDHARTH RAMBHAI | 2015-16 | PG | University of Southern California | 2016 |
...
| 20 | SONI SAPAN | 2015-16 | PG | University of Toronto | 2017 |
|  |  |  |  |  |  |
| Note: Please enter data for students who have graduated in year 2015-16 from your institute and got admitted in PG/PhD program of a top institution |  |  |  |  |  |
| 2. Institutions ranked as top institutions in the following ranking bodies namely India Ranking 2016, QS World Ranking 2016, THE World University Ranking 2016. |  |  |  |  |  |
```

### Final Output
The final output is the markdown table with the correct formatting and no extra text.

### Additional Output (Split into smaller sections)
Since the original output exceeded the 256-token limit, we will split it into smaller sections with headings.

### Section 1: Table Header and First 10 Rows
```markdown
| S.No. | Name of the student of your institution | Graduating year of the student | PG/PhD program in where student has been admitted | Name of the top university/institutions | Year of admission |
|---|---|---|---|---|---|
| 1 | BHUTIYA SIDDHARTH RAMBHAI | 2015-16 | PG | University of Southern California | 2016 |
| 2 | MITI JAGAN MAZMUDAR | 2015-16 | PG | University of Waterloo | 2016 |
| 3 | TRIVEDI HARSH JIGISH | 2015-16 | PG | Stony Brook University | 2016 |
| 4 | ARCHIT MANISHKUMAR GAJJAR | 2015-16 | PG | University of Houston | 2017 |
| 5 | DOSHI PAL PANKAJ | 2015-16 | PG | University of Maryland, College Park | 2016 |
| 6 | TALLURI SACHEENDRA | 2015-16 | PG | Delft University of Technology | 2016 |
| 7 | RACHIT MISHRA | 2015-16 | PG | University of Texas Dallas | 2016 |
| 8 | BANSARI S RAO | 2015-16 | PG | University of Florida | 2016 |
| 9 | GAURAV MAHESHWARI | 2015-16 | PG | Rheinische Friedrich-Wilhelms-Universität Bonn | 2016 |
| 10 | THAKKER SHIVANI DHIRENBHAI | 2015-16 | PG | XLRI - Xavier School of Management, Jamshedpur | 2016 |
```

### Section 2: Next 10 Rows
```markdown
| 11 | K. VEDASAGAR | 2015-16 | PG | Johns Hopkins University | 2016 |
| 12 | DHRUMIL NIMISH SHAH | 2015-16 | PG | California State University | 2016 |
| 13 | TAKSHAK PARMAR | 2015-16 | PG | Indiana University-Purdue University Indianapolis | 2016 |
| 14 | DEVANSHU JAIN | 2015-16 | PG | University of Pennsylvania | 2016 |
| 15 | MUTYALA BHARATH | 2015-16 | PG | Drexel University | 2016 |
| 16 | KARTIKEYA CHATURVEDI | 2015-16 | PG | XLRI - Xavier School of Management, Jamshedpur | 2016 |
| 17 | VRAJ SALIL DELHIVALA | 2015-16 | PG | Arizona State University | 2016 |
| 18 | SAI NIKHIL REDDY DEVIREDDY VENKATA | 2015-16 | PG | New York University | 2016 |
| 19 | KUNAL JHA | 2015-16 | PG | Rheinische Friedrich-Wilhelms-Universität Bonn | 2016 |
| 20 | SONI SAPAN | 2015-16 | PG | University of Toronto | 2017 |
```

### Section 3: Table Footer
```markdown
|  |  |  |  |  |  |
| Note: Please enter data for students who have graduated in year 2015-16 from your institute and got admitted in PG/PhD program of a top institution |  |  |  |  |  |
| 2. Institutions ranked as top institutions in the following ranking bodies namely India Ranking 2016, QS World Ranking 2016, THE World University Ranking 2016. |  |  |  |  |  |
```
