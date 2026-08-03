---
title: "DS401 Causal Inference Autumn Semester 2026-27"
url: "https://ecampus.daiict.ac.in/webapp/intranet/index.jsp"
category: "Academics - Course Policies"
scraped_by: "Squad D Scraper"
scraped_date: "2026-07-23"
team: "Squad D"
source_type: "PDF"
pdf_name: "DS401__2026-27__DS401_Causal_Inference - Abhishek Tripathy.pdf"
course_code: "DS401"
semester: "Autumn Semester 2026-27"
authorization: ["public"]
---

# DS401: Causal Inference

## Course Overview

| Field | Details |
|---|---|
| **Course Code** | DS401 |
| **Course Name** | Causal Inference |
| **Instructor(s)** | Abhishek Tripathy (FB1-1205, abhishek_tripathy@dau.ac.in) |
| **Credits** | 4 (Lecture: 3 hrs/week, Tutorial: 0 hrs/week, Practical: 1 hr/week) |
| **Semester Offered** | Autumn |
| **Type** | Technical Elective |
| **Program(s)** | BTech ICT, Mathematics and Computing (3rd Sem); MSc Data Science (3rd Sem) |
| **Year / Semester in Program** | 3rd Semester |
| **Associated Lab** | Embedded lab/tutorial component (case studies and/or datasets using R or Python) |
| **Prerequisites** | Exposure to the basics of Probability and Statistics is highly recommended |
| **Foundation For** | None stated |

---

## Course Description

We live in a world that is full of data, ranging from economic statistics of firms to items in the national budget, and from biomedical experiments to even the text from newspaper articles. Pick out any two variables from any dataset and there is a correlation between them - however strong or weak. However, we need advanced tools to infer if one variable causes the other. In this course, we aim to learn precisely such tools which help us answer a basic question: Does X cause Y? The implications of finding an answer are wide-ranging. Policymakers and think-tanks are increasingly turning to professionals and researchers who are trained in methods of statistical analysis and causal inference for evaluating existing policies and/or designing new policies.

This course will expose the student to the basics of the vast and still-evolving field of causal inference. We will begin with a discussion on regressions and methods of inference of coefficients along with hands-on exercises. Then we will learn about the foundational theories of causal inference: the theory of potential outcomes and Directed Acyclic Graphs (DAGs), both of which sit at the heart of theoretical work that has seen people win Nobel prizes in economics. We will then move on to an introduction to various tools for inferring causality from experimental and non-experimental data: Randomized Controlled Trials, Instrumental variables, Matching, Differences-in-differences, Regression Discontinuity designs, and Synthetic control methods. The final module of the course will focus exclusively on the rapidly evolving sub-field of Causal machine learning.

*Note (as stated in source): We will not be proving theorems in this course. The idea is to gather an intuitive understanding of what each technique does and the various types of applications of the technique with basic statistics/algebra. If someone is interested in exploring advanced techniques or concepts, the instructor will provide adequate support.*

---

## Course Outcomes (COs)

*Note: The source document states outcomes as a narrative paragraph rather than a numbered CO list; it is reproduced below as CO1.*

| CO | Description |
|---|---|
| CO1 | On successful completion of the course, the student will have developed the ability to think about real-world problems using the framework of causality. Students will be able to break down complex problems based on sound economic logic, arrange data for analyzing the problem and finding a solution, and offer potential solutions based on the usage of one or more of the causal inference techniques learned from this course, putting them in a strong position to provide end-to-end advice on solutions to problems facing organizations, governments, and society in general |

---

## Program Outcome Mapping (PO Mapping)

| PO1 | PO2 | PO3 | PO4 | PO5 | PO6 | PO7 | PO8 | PO9 | PO10 | PO11 | PO12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | X | | X | X | X | | | | | | |

---

## Course Structure

| Unit | Topic | No. of Lectures |
|---|---|---|
| Module 1: Foundations | Regression overview: Introduction to linear and non-linear regression techniques including data types (panel, cross-sections), OLS/logistic/probabilistic regressions with inference of coefficients, hypothesis testing (t-tests, F-tests), interpretation of interacted terms, tests of equality of coefficients and linear combinations of coefficients (6 lectures). Potential outcomes model: theory of potential outcomes, identification, various types of identification, treatment effects (ATE, CATE, LATE, ATT) (4 lectures). Causal diagrams: Directed Acyclic Graphs, confounders, back-door criterion, front-door criterion (3 lectures) | 13 |
| Module 2: Causal inference with experimental data | Randomized Controlled Trials (RCTs): experimental design, randomization, balance tests, regressions and inference, external validity (3 lectures). Special types of RCTs: stratified RCTs, pairwise randomized experiments (2 lectures) | 5 |
| Module 3: Causal inference with non-experimental data | Instrumental variable designs: research design, assumptions, two-stage least squares, diagnostics (4 lectures). Matching designs: propensity score matching, coarsened exact matching (2 lectures). Differences-in-Differences designs: research design, assumptions and diagnostics, inference of coefficients, introduction to staggered differences-in-differences (5 lectures). Regression Discontinuity designs (RDD): research design, assumptions, Sharp RDD and Fuzzy RDD (4 lectures) | 15 |
| Module 4: Causal inference and Machine learning | Causal Machine learning: doubly de-biased ML, random and causal forests, doubly robust estimation, LASSO and IV-LASSO | 5 |
| **Total** | | **38** |

---

## Weekly Schedule / Lecture Plan

*Note: No weekly (dated) lecture schedule is available in the source document; only the module-wise lecture distribution shown above is provided.*

---

## Evaluation / Grading Scheme

*(Tentative, as stated in source)*

| Component | Weightage |
|---|---|
| Quizzes (5 instances) | 10% |
| Group project | 40% |
| In-semester examination | 20% |
| End-semester examination | 30% |
| **Total** | **100%** |

---

## Textbooks and References

### Textbook(s)

1. Nick Huntington-Klein, *The Effect: An Introduction to Research Design and Causality*, Chapman and Hall/CRC, 2021 (free e-version at https://theeffectbook.net/).

### Reference Books

1. Scott Cunningham, *Causal Inference: The Mixtape*, Yale University Press, 2021 (free e-version at https://mixtape.scunning.com/).
2. J. Pearl and D. McKenzie, *The Book of Why: The New Science of Cause and Effect*, Penguin, 2018.
3. Guido Imbens and Donald B. Rubin, *Causal Inference for Statistics, Social and Biomedical Sciences*, Cambridge University Press.
4. M. A. Hernan and James M. Robins, *Causal Inference. What if?*, Chapman and Hall/CRC, 2025 (free e-book at https://www.hsph.harvard.edu/miguel-hernan/causal-inference-book/).

### Online Resources

- [The Effect (free e-version)](https://theeffectbook.net/)
- [Causal Inference: The Mixtape (free e-version)](https://mixtape.scunning.com/)
- [Causal Inference. What if? (free e-book)](https://www.hsph.harvard.edu/miguel-hernan/causal-inference-book/)

---

## Program Structure Context

DS401 is a Technical Elective for BTech ICT and Mathematics and Computing students (3rd Semester) and MSc Data Science students (3rd Semester), offered in the Autumn semester.

---

## Additional Notes

- **Reference guidance (as stated in source)**: R1 is most comparable to the main textbook, though oriented toward developing an advanced understanding; the student can clarify understanding of concepts from the main text with R1 fairly seamlessly. R2 is recommended for casual reading and for developing an intuitive understanding of the topic devoid of mathematical notations. R3 and R4 provide a rigorous technical exposure and may be referred to only for clarifying concepts at an advanced level.
- **Lab/Tutorial Component**: Lab sessions will involve students working on case studies and/or datasets to gain practical exposure to causal inference techniques using R; students proficient in Python are free to use it instead, though the instructor will primarily assist with R. Students are encouraged to construct their own datasets through web scraping in line with personal interests, or to use publicly available datasets with appropriate citations.
- **Comments**: Some classes will involve the use of cases or open policy issues/problems to help think about the application of specific techniques.
- **Group Project details**: The class will be divided into groups working with individual accountability. Students are encouraged to be creative in choosing a project topic (economics, public policy, or any field of interest), justifying its academic importance via literature. Marks are awarded for: clarity on the topic (5%), ability to break down the problem using solid literature-based logic (5%), justified application of causal inference techniques (15%), and quality of answers to questions during the group presentation (15%). No separate project report is required, but a detailed project presentation is required, including a preliminary presentation for instructor feedback and up to one in-person consultation with the instructor.
- **Note on the usage of AI (as stated in source)**: Students are discouraged from using available LLMs for the course project or anywhere in the classroom. Detection of AI-generated content in any evaluative component will result in strict penalties, including but not limited to a failing grade for the course.

---

## Downloads and Resources

| Resource | Type | Link |
|---|---|---|
| DS401__2026-27__DS401_Causal_Inference - Abhishek Tripathy.pdf | PDF | [Download PDF]({ORIGINAL_URL}) |

---

## Document Metadata

| Field | Value |
|---|---|
| **Source PDF** | DS401__2026-27__DS401_Causal_Inference - Abhishek Tripathy.pdf |
| **Scraped Date** | 2026-07-23 |
| **Intranet Portal** | [DA-IICT Intranet](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |
| **Academic Guidelines** | [DAU Academics](https://daiict.ac.in/academics) |
