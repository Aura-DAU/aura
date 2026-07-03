---
title: "Visvesvaraya Ph.D. Scheme"
url: "https://www.daiict.ac.in/visvesvaraya-phd-scheme"
category: "Admissions"
scraped_by: "Khushi Gandhi"
scraped_date: "2026-06-01"
team: "Team A"
last_fixed: "2026-07-02"
fixes_applied: ['OCR_NOISE']
---

<think>
Okay, let's tackle this. The user wants me to clean up the raw text from the PDF into structured Markdown following their specific rules. First, I need to make sure I understand all the rules they've given. Let me go through them again.

Rule 1: Output only the markdown body. No frontmatter or explanations. Got it. So I can't add any extra text beyond the structured content.

Rule 2: Use H1 for the title. The title here is "Visvesvaraya Ph.D. Scheme". I'll start with that.

Rule 3: H2 for major sections. The main sections here are Overview, About the Scheme, Eligibility Criteria, Fellowship and Other Benefits, Duration of Fellowship, Selection Process, Important Dates, List of Beneficiaries, Related Links, and Downloadable Resources. Wait, the original text has sections like "Main Content" with subsections. I need to reorganize those into proper H2s.

Looking at the raw text, the first section is "Overview" which is an H1. Then under "Main Content", there's "About the Scheme", which is a repetition of the overview. Maybe that's a duplicate. I should check if that's necessary. The user says to preserve all content, so I'll keep it but structure it properly.

Next, "Eligibility Criteria" is a major section (H2), then "Fellowship and Other Benefits" as another H2. Then "Duration of Fellowship" as H2. "Selection Process" as H2, with subsections like "Entrance Test waiver" and "Interview" as H3s. "Important Dates" as H2 with a table. "List of Beneficiaries" as H2, "Related Links" as H2, and "Downloadable Resources" as H2.

I need to make sure each H2 is properly placed. Also, check for any garbled text. For example, in the "Thrust Research Areas", there's a list that's a bit long. I need to split it into Priority Areas and Emerging Areas as H3s under the Thrust Research Areas H2. The user mentioned splitting large sections into H3s if they exceed ~256 tokens. The Emerging Areas list is quite long, so maybe split it into multiple H3s? Wait, the user says each H2/H3 should fit within ~256 tokens. Let me count the words in the Emerging Areas. It's a long list, but since it's a list, maybe it's okay as a single H3. Alternatively, split into multiple H3s if needed. But the user says to split large sections with additional H3s. Hmm. The Emerging Areas list is one paragraph, but it's a list of items separated by commas. Maybe it's better to keep it as a single H3 with the list. I'll check the token count later.

Also, there are some OCR errors. For example, "Visvesvary" in the NOC link. The correct spelling is "Visvesvaraya". I should correct that. The user allows fixing OCR typos if I'm 100% certain. Since "Visvesvary" is likely a typo for "Visvesvaraya", I'll correct it.

In the "Duration of Fellowship" section, the text says "Support will be provided upto 5 years or the Ph.D. duration whichever is lesser." The word "upto" should be "up to" with a space. That's a minor correction.

The "Important Dates" table has a column with "TBD". I need to make sure the table is properly formatted in Markdown. The original has two columns, but the second row has "TBD" which is okay.

Also, check for any repeated headers. The "Overview" and "About the Scheme" both have similar content. The user says to remove repeated headers. So maybe the "About the Scheme" section under "Main Content" is redundant. The user says to preserve all content, but remove repeated headers. So I'll keep the content but structure it under the appropriate H2.

In the "Eligibility Criteria" section, there are subsections for Full-time and Part-time. Those should be H3s under the main H2 "Eligibility Criteria".

For the "Fellowship and Other Benefits", the user has (a) and (b) for Full-time and Part-time. These should be H3s under the main H2.

The "Selection Process" has subsections like "Entrance Test waiver" and "Interview", which should be H3s.

The "List of Beneficiaries" section is a placeholder, so I'll keep it as is.

Now, let's start structuring the Markdown.

Start with the H1 title. Then the Overview as H2. Wait, the original has an H1 for Overview. But the user's example shows the title as H1, then sections as H2. Wait, the user's instruction says to use H1 for the document title once at the top. The original text has an H1 for "Overview", but that's not correct. The title should be the document title, which is "Visvesvaraya Ph.D. Scheme". So the first line should be # Visvesvaraya Ph.D. Scheme. Then the Overview section as H2.

Wait, looking back at the user's example, the title is H1, then sections like Overview, Eligibility, etc., as H2. So in the raw text, the first line is # Overview, but according to the rules, the title should be H1. So I need to correct that. The user's example shows the title as H1, then sections as H2. So the first line should be the title as H1, then the Overview section as H2.

So the structure would be:

# Visvesvaraya Ph.D. Scheme

## Overview

[content]

## About the Scheme

[content]

Wait, but the original has "Overview" as an H1. But according to the rules, the title is H1. So the user's raw text might have an error here. The correct approach is to make the title H1, then the Overview as H2. So I'll adjust that.

Next, the "Main Content" section in the raw text includes "About the Scheme", which is a repetition of the overview. Since the user says to remove repeated headers, I'll merge that into the Overview section. Wait, the original has "Overview" as an H1 and then under "Main Content", "About the Scheme" as another H2. Since they're similar, I should combine them into one section under H2 Overview.

Wait, the user's instruction says to remove repeated headers. So if "Overview" and "About the Scheme" are the same, I should keep one. But the user says to preserve all content. Hmm. The original text has "Overview" as an H1 and then "About the Scheme" as an H2 with the same content. Since the user says to remove repeated headers, I'll keep the content under the H2 "Overview" and remove the duplicate.

So the structure would be:

# Visvesvaraya Ph.D. Scheme

## Overview

[content from both Overview and About the Scheme sections]

Then proceed with the other sections.

Next, the "Eligibility Criteria" as H2, with subsections for Full-time and Part-time as H3s.

"Fellowship and Other Benefits" as H2, with subsections for Full-time and Part-time as H3s.

"Duration of Fellowship" as H2.

"Selection Process" as H2, with subsections for Entrance Test waiver and Interview as H3s.

"Important Dates" as H2 with the table.

"List of Beneficiaries" as H2.

"Related Links" as H2.

"Downloadable Resources" as H2.

Now, checking for any garbled text. For example, in the Emerging Areas list, there's "A speech to speech translation system enhanced with prosodic information for converting speech in english and speech in assamese and vice versa,". The user says to preserve all numbers, names, etc., exactly. So I'll keep it as is.

In the NOC link, "Visvesvary" should be corrected to "Visvesvaraya".

Also, in the "Duration of Fellowship" section, "upto" should be "up to".

In the "Selection Process" section, the note about the interview being held physically at DA-IICT, Gandhinagar. The user says to remove footers, page numbers, etc. But this is part of the content, so it should be kept.

Now, formatting the tables. The "Important Dates" table has two columns. The original has:

|  |  |
| --- | --- |
| Application Deadline | **30 May 2025** |
| Announcement of the Shortlisted Candidates | **10 June 2025** |
| Written Examinations/Interviews | **15 June 2025** |
| Announcement of Results | **TBD** |

I need to make sure the table is properly formatted with pipes and headers. The user's example shows the table with | col | col | format. So that's correct.

Also, check for any control characters or OCR noise. For example, in the raw text, there's "reg1strat1un" which should be "registration". The user allows fixing OCR typos if certain. But in the provided text, I don't see such typos. The only possible one is "Visvesvary" which I corrected.

Now, putting it all together. Let's start writing the Markdown.

First, the title as H1.

Then the Overview section combining the content from the original Overview
