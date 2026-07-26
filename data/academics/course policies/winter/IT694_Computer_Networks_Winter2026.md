---
title: "IT694 Computer Networks Winter 2026"
url: "https://ecampus.daiict.ac.in/webapp/intranet/index.jsp"
category: "Academics - Course Policies"
scraped_by: "Squad D Scraper"
scraped_date: "2026-07-25"
team: "Squad D"
source_type: "PDF"
pdf_name: "IT694_ComputerNetworks_Winter2026 - kalyan sasidhar P S.pdf"
course_code: "IT694"
semester: "Winter 2026"
---

# IT694: Computer Networks

## Course Overview
| Field | Details |
|---|---|
| **Course Code** | IT694 |
| **Course Name** | Computer Networks |
| **Instructor(s)** | Prof. P.S. Kalyan Sasidhar, Office 2109, Faculty Block-2, Extn. 560, email: kalyan_sasidhar@daiict.ac.in |
| **Credits** | 3-0-2-4 (3 Lecture hours and 2 Lab hours) |
| **Semester Offered** | Winter 2026 |
| **Type** | Core |
| **Program(s)** | MSc IT |
| **Year / Semester in Program** | Semester II |
| **Associated Lab** | Integrated lab component (2 lab hours/week; basic LAN hardware, configuration, and network simulation tools) |
| **Prerequisites** | Not stated in source document |
| **Foundation For** | Not stated in source document |

## Course Description
This course will cover the fundamental principles of wired computer networks with focus on layered architecture, protocols, implementation and issues specific to the Internet. The objective is to provide an understanding of how the Internet works, including how data flows from a source to a destination. Focus will also be laid on certain topics such as network design and automation, network management, administration and debugging, which are ideally required for networking IT professionals.

The associated laboratory component is designed to expose students to basic LAN hardware and configuration, and network simulation tools for the analysis of traffic and network protocols. Cisco laboratory exercises will be strongly referred to in order to provide industry-level exposure to real-life networking scenario-based labs.

**Aims and Objectives:** The Internet is the largest engineered system being utilized by billions of users through their portable devices, including laptops, tablets, and smartphones. The inner workings of such a large system with many diverse components and uses need to be understood. This includes the guiding principles and structure that can provide a foundation for understanding such an amazingly large and complex system.

## Course Outcomes (COs)
At the end of the course, students are expected to:

| CO# | Description |
|---|---|
| 1 | Understand the TCP/IP Internet reference Model |
| 2 | Learn commonly used network protocols and their design |
| 3 | Be able to design and develop network applications |
| 4 | Be exposed to traffic engineering and multimedia networking concepts |
| 5 | Measure performance of protocols using analytical methods and simulation tools |

## Program Outcome Mapping (PO Mapping)
| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| X | | | X | X | | | | X | | | |

Verified via pdfplumber table extraction (the source text layer for this row is severely column-jumbled; the table structure was used to establish correct positions): P1, P4, P5, and P9 are marked X; all other columns are blank. No PSO table is present in the source.

## Course Structure
| Unit | Topic | No. of Lectures |
|---|---|---|
| 1 | Overview: Internet – Bird's Eye View, History; Internet Layered Architecture: OSI and TCP/IP architectures; Packet Switching, Best Effort Services | 6 |
| 2 | Network Applications: Client-Server Applications; Chat Application Design, Socket Programming; SFTP File Transfer Protocol; Domain Name Service, Mail, SMTP; Peer to Peer Search, Distributed Hash | 6 |
| 3 | End to End Issues: Transport Layer Basics; Reliability; Connectionless and Connection Oriented Transport; TCP and UDP protocols; Congestion Management; TCP Performance Measure | 6 |
| 4 | Routing and Congestion: Introduction; Scheduling, Best Effort Service; Scheduling for Guaranteed Service, Switching; Packet Switching, Batcher Banyan Switch; Routing – Introduction, Multicast, Broadcast; Addressing, CIDR, IP Protocol IPv4, IPv6; Hierarchical Routing, BGP, Mobile Routing; Control and Data Path, Open Flow; Software Defined Networking | 8 |
| 5 | Link Layer Technologies: Introduction; Media Access Protocols, ALOHA; IEEE 802.3 Ethernet Protocol, MACA; Switched LAN, Virtual LANs | 6 |
| 6 | Network Design and Automation: Network Automation and Programmability Tools and Techniques (Python, Ansible, Puppet and Chef); Application Programming Interface (RESTful API request and response); Green and Sustainable Network Infrastructure Design (advanced cooling techniques and power management) | 4 |
| 7 | Content Distribution Networks: Architecture and protocols; Video Streaming, DASH | 3 |
| 8 | Network Management: Network Debugging; Revision | 3 |

## Weekly Schedule / Lecture Plan
Note: No weekly schedule with dates is available in the source document. A "Tentative Lecture Outline" with per-unit lecture counts is provided instead (see Course Structure above).

## Evaluation / Grading Scheme
| Component | Weightage |
|---|---|
| In-Sem I | 15% |
| In-Sem II | 20% |
| End Sem | 35% |
| Labs | 25% |
| Quizzes | 5% |

Total: 100% (reconciles correctly). Verified via pdfplumber table extraction, since the raw text layer interleaves the "Evaluation Scheme" table with unrelated "Aims and Objectives" paragraph text due to a layout/column extraction artifact in the source PDF.

## Textbooks and References
**Textbook**
1. James F. Kurose and Keith W. Ross. 2016. *Computer Networking: A Top-Down Approach* (7th ed.). Pearson.

**Reference Books**
1. Douglas E. Comer. 2013. *Internetworking with TCP/IP* (6th ed.). Addison-Wesley Professional.
2. Andrew S. Tanenbaum and David J. Wetherall. 2010. *Computer Networks* (5th ed.). Prentice Hall Press, Upper Saddle River, NJ, USA.
3. Larry L. Peterson and Bruce S. Davie. 2011. *Computer Networks, Fifth Edition: A Systems Approach* (5th ed.). Morgan Kaufmann Publishers Inc., San Francisco, CA, USA.

## Program Structure Context
IT694 is a core course for MSc IT students in Semester II, combining lecture and lab instruction in fundamental computer networking. It sits within the postgraduate IT curriculum and connects theoretical networking principles (layered architecture, protocols) with hands-on Cisco-based lab exercises and modern topics such as network automation and software-defined networking.

## Additional Notes
- **Course code mismatch/discrepancy in placement description**: page 1 of the source lists "Course Placement: MSc IT, Semester-II" while page 2 lists "Course Placement: MSc IT Core." Both are captured above (Program = MSc IT; Semester = II; Type = Core) as they appear complementary rather than contradictory, but this is flagged per instructions.
- **Extraction difficulty**: The plain `pdftotext -layout` output for page 2 of this PDF severely interleaves two side-by-side text blocks (the "Aims and Objectives" paragraph and the "Evaluation Scheme" table, and separately the "Course outcomes" list and "Textbook/References" list), producing scrambled, character-interleaved text (e.g. "Ithne- gSueidmin gI princip"). This was cross-checked and resolved using pdfplumber's table and text extraction, which correctly isolated the Evaluation Scheme percentages and the PO mapping row. Course outcomes and course description paragraphs were reconstructed by comparing the page 0 and page 1 text (which duplicate much of the same content in cleaner form) against the jumbled page 1 text.
- Evaluation weightages sum correctly to 100%.
- Course Conduct and Grading Policy (attendance ≥70% requirement, lab completion requirement, plagiarism policy) is captured in Additional Notes as it does not fit the standard template sections: students must maintain at least 70% attendance or receive an F grade (subject to supersession by an institute-wide policy to be communicated separately); all lab assignments must be completed or zero marks are awarded for the lab component, with one makeup lab session at the end of the semester (additional makeup sessions possible for Dean AP-approved medical cases); any detected plagiarism/copying in exams or lab submissions results in zero marks for the complete lab segment (25%) or the respective exam component, plus a report to the Dean AP for possible further action.

## Downloads and Resources
| Resource | Type | Link |
|---|---|---|
| IT694_ComputerNetworks_Winter2026 - kalyan sasidhar P S.pdf | PDF | [Download IT694_ComputerNetworks_Winter2026 - kalyan sasidhar P S.pdf](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |

## Document Metadata
| Field | Value |
|---|---|
| **Source PDF** | IT694_ComputerNetworks_Winter2026 - kalyan sasidhar P S.pdf |
| **Scraped Date** | 2026-07-25 |
| **Intranet Portal** | [DA-IICT Intranet](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |
| **Academic Guidelines** | [DAU Academics](https://daiict.ac.in/academics) |
