---
title: "Courses Through CEP & AIP"
url: "https://www.daiict.ac.in/courses-through-aip-cep"
category: "CEP"
scraped_by: "Khushi Gandhi"
scraped_date: "2026-06-01"
team: "Team A"
last_fixed: "2026-07-02"
fixes_applied: ['OCR_NOISE']
---

<think>
Okay, let's start by looking at the user's request. They want me to structure the provided raw text into clean Markdown following specific rules. The main goal is to create a structured document for the AURA RAG system at Dhirubhai Ambani University. 

First, I need to identify the title. The user provided "Courses Through CEP & AIP" as the title, so I'll start with that as an H1.

Next, the raw text has sections like Overview, CEP, AIP, Core Responsibilities, Contact Us, etc. I need to convert these into H2 and H3 sections as per the rules. For example, "Overview" is already an H2 in the raw text, so I'll keep that. 

Looking at the CEP and AIP sections, they each have their own content. The user mentioned that H3 should be subsections within each major section. However, in the raw text, CEP and AIP are under Main Content as H2s. Wait, the user's example shows that the main sections are H2s. So I need to check if "CEP" and "AIP" should be H2s under the Main Content H2. But in the provided example, the user has "Main Content" as an H2, and then CEP and AIP as H3s. Wait, no, looking back, the user's example shows:

# Overview

## CEP

## AIP

So maybe the Main Content is not an H2. Wait, the user's raw text starts with # Overview, then ## CEP, then ## AIP. So I should follow that structure. The user's instruction says to use H2 for major sections like Overview, Eligibility, etc. So the initial Overview is H1, then the sections like CEP, AIP, Core Responsibilities, Contact Us, etc., should be H2s.

Wait, the user's raw text has:

# Overview

DAIICT has been very active in the area of the CEP. ... 

## CEP

DAIICT has been very active in the area of the CEP. ... 

So the first section is an H1, then the next sections are H2s. So the structure is:

H1: Courses Through CEP & AIP

H2: Overview

H2: CEP

H2: AIP

H2: The core responsibilities and functions of the CEP & AIP include:

H2: Contact Us

H2: Documents/Forms

H2: AIP 2025-26

H2: CEP 2025-26

H2: AIP 2025-26

H2: 2025-26

H2: 2024-25

H2: 2023-24

H2: 2022-23

H2: CEP Committee

H2: Related Links

H2: Downloadable Resources

But the user's rules say to use H2 for major sections and H3 for subsections. However, in the raw text, some sections like "2025-26" under the AIP 2025-26 table might be H3s. Wait, the user's example shows that under AIP 2025-26, there's a list of workshops with years. Maybe those should be H3s under the AIP 2025-26 H2.

Also, the user mentioned that each H2/H3 should be within ~256 tokens. I need to check if any sections are too long and split them if necessary. For example, the "CEP" section has a lot of text. Let me see: the CEP section starts with a paragraph about DAIICT's activity, then another paragraph about the CEP Centre's mission. Maybe splitting into H3s for each paragraph.

Wait, the user's instruction says to split large sections with additional H3s. So if a section is too long, split into H3s. For example, the CEP section has two paragraphs. The first is about DAIICT's activity, the second is about the CEP Centre's mission. So maybe split into two H3s.

Similarly, the AIP section has two paragraphs. The first about being an Anchor Institute, the second about the program's objectives. So split into H3s.

The core responsibilities section is a bullet list. Maybe keep it as is under an H2.

The contact us section has a phone and email. Keep as H2.

Documents/Forms has CEP Forms and AIP Forms as H3s.

The AIP 2025-26 and CEP 2025-26 sections have tables. The user's example shows that the AIP 2025-26 table is under an H2, and the 2025-26 workshops are under another H2. Wait, in the raw text, after the AIP 2025-26 table, there's a section labeled "### 2025-26" with bullet points. That should be an H3 under the AIP 2025-26 H2.

Similarly, the 2024-25, 2023-24, etc., sections are under the same H2 as the 2025-26 workshops. Wait, in the raw text, after the AIP 2025-26 table, there's a section labeled "### 2025-26" with bullet points. Then "### 2024-25", etc. So those should be H3s under the AIP 2025-26 H2. But the user's example shows that the AIP 2025-26 is an H2, and the subsequent years are H3s. So I need to adjust that.

Wait, looking at the user's provided example, the structure is:

# Courses Through CEP & AIP

## Overview

## CEP

### [Subsection]

## AIP

### [Subsection]

## Core Responsibilities...

But in the raw text, after the AIP 2025-26 table, there's a section labeled "### 2025-26" with bullet points. That should be an H3 under the AIP 2025-26 H2. Similarly for the other years.

Also, the CEP Committee section has Head and Members as H3s.

Now, checking for garbled text. The user mentioned removing control characters and OCR noise. Looking through the text, I don't see any obvious OCR errors like "reg1strat1un" that need fixing. The email addresses are written with [at] and [dot], which should be converted to @ and . as per standard. For example, [cep[at]daiict[dot]ac[dot]in] becomes cep@daiict.ac.in.

Also, the user wants to preserve all numbers, names, dates, etc., exactly. So I need to make sure that course titles and years are kept as they are.

For the tables, the user wants them converted into proper Markdown tables. The AIP 2025-26 table has a row with "More information to follow" and empty cells. I'll keep that as is. The same for the CEP 2025-26 table.

The user also wants to remove repeated headers, page numbers, footers, etc. In the raw text, there's a line "## The core responsibilities and functions of the CEP & AIP include:" which is a heading but the content is a bullet list. So that should be an H2.

The contact us section has a phone number with (+91) 079 - 68261565. Need to make sure the formatting is correct.

For the downloadable resources, the user has a list of links. The example shows that these are under H2: Downloadable Resources, with bullet points.

Now, putting it all together:

- Start with H1: Courses Through CEP & AIP
- H2: Overview
- H2: CEP
  - H3: [Subsection 1]
  - H3: [Subsection 2]
- H2: AIP
  - H3: [Subsection 1]
  - H3: [Subsection 2]
- H2: Core Responsibilities and Functions of CEP & AIP
- H2: Contact Us
- H2: Documents/Forms
  - H3: CEP Forms
  - H3: AIP Forms
- H2: AIP 2025-26
  - Table
  - H3: 2025-26 (workshops)
  - H3: 2024-25
  - H3: 2023-24
  - H3: 2022-23
- H2: CEP 2025-26
  - Table
- H2: CEP Committee
  - H3: Head
  - H3: Members
- H2: Related Links
- H2: Downloadable Resources
  - Bullet points

I need to ensure that each H2 is a major section, and H3s are subsections. Also, check that all tables are properly formatted with pipes and headers. For example, the
