---
title: "Control of Autonomous Systems"
url: "https://intranet.daiict.ac.in/academics/Course_Booklet_for_Autumn_2025-26.pdf"
category: "Academics"
scraped_by: "Squad D Scraper"
scraped_date: "2026-06-01"
team: "Squad D"
source_type: "PDF"
pdf_name: "Course_Booklet_for_Autumn_2025-26.pdf"
---

# Control of Autonomous Systems (IE415)

## Overview

This document presents the detailed policy and syllabus structure for the course Control of Autonomous Systems (IE415). It includes details on course objectives, credits, prerequisites, syllabus content, evaluation schemes, and contact information where available.

## Main Content

| Course Title | Control of Autonomous Systems |  |  |
|---|---|---|---|
| Course Code | IE415 | Credit Structure | 3-0-2-4 (L-T-P-C) |
| Category | Core / Elective | Semester | Autumn Semester (AY 25-26) -V |
| Program | B.Tech (ICT) - Elective, B.Tech (ICT with Minor in RAS) -Core |  |  |
| Prerequisites | Basic Linear Algebra, Signals & Systems, Programming |  |  |
| Course Objectives/ Brief Course Description | Course objective ● To understand the different ways of system representations such as transfer function representation and state space representations and to assess the system dynamic response. ● To assess the system performance using time domain analysis and methods for improving it. ● To assess the system performance using frequency domain analysis and techniques for improving the performance. ● To design various controllers and compensators to improve system performance. ● To find models of dynamical systems, such as robots and quadrotors, and analyze their stability. ● To study Path Planning algorithms that describe the motion of a robot between two points and produces commands so that the robot has safe and optimal motion. ● To design state estimation techniques such as Kalman and Bayes filters Course Overview Autonomous systems are machines that can perform tasks and operate in an environment independently without human intervention and control. The autonomous systems, such as unmanned aerial vehicles (UAV), autonomous cars, wheel, and legged robots, etc., can potentially replace humans from dull, dangerous, and dirty tasks. Therefore, the development and control of autonomous systems is a rapidly-growing field and highly applied in the industries. The course intends to develop an understanding of dynamics of robot manipulators, mobile robots, and drones (quadrotors, AGVs, AUVs), controls for robotic systems for motion-planning, collision avoidance, trajectory optimization, grasping and manipulating objects. The course will include simulations related to dynamics, trajectory generation, motion planning, and control of autonomous systems, such as robots, manipulators and drones. This course will introduce the fundamental and algorithmic principles behind the dynamics and control of autonomous systems. The course will also allow students to get hands-on experience through project- based assignments with the wheeled robot and quadrotor. |  |  |


---
*Page Split*
---

| Evaluation/
Grading Policy | ● Multiple (Surprise) Quizzes – 10%
● Multiple Assignments including group or mini-project assignments – 10%
● Lab (Assignments, Exams and Projects) – 10%
● Two In-Semester exams – 40% (20% each)
● One End-Semester Examination – 30% |
|---|---|
| Course Materials/ References | • Saeed B. Niku, Introduction to Robotics: Analysis, Control, Applications, 3rd Ed., Wiley, 2019. • Illah R. Nourbaksh and Roland Siegwart, Introduction to Autonomous Mobile Robots. • Steven M. LaValle, Planning Algorithms, Cambridge University Press, 2006. • Timothy D. Barfoot, State Estimation for Robotics, Cambridge University Press,2017 • Hassan Khalil, Nonlinear Systems, Third Edition, Pearson • Mark W. Spong, Seth Hutchinson, and M. Vidyasagar, Robot Dynamics and Control, John Wiley & Sons, Inc • Peter Corke, Robotics, Vision and Control, Fundamental Algorithms, 2nd Ed., Springer, 2017. • B. Siciliano, L. Sciavicco, L. Villani, and G. Oriolo, Robotics - Modelling, Planning and Control, 1st Ed., Springer, 2009. • Katsuhiko Ogata, Modern Control Engineering, Prentice Hall of India Pvt. Ltd., 3rd edition, 1998. [Reference Book] • I. J. Nagrath and M. Gopal, Control Systems Engineering, New Age International (P) Limited, Publishers, 5th edition, 2009. [Reference Book] Relevant documents and research papers shared from time to time |
| Detailed Course Content | APPENDIX |


Course Outcome:  
CO1. Improve the system performance by selecting a suitable controller and/or a compensator for a 
specific application

CO2. Find model of the dynamical systems, such as a robots and quadrotors, and analyse their 
stability.

CO3. Study and implement Path Planning algorithms that describe the motion of a robot between two 
points and generate trajectories such that the robots have safe and optimal motion.

CO4. Design state estimation techniques such as Kalman and Bayes filters.

---
*Page Split*
---

POs-COs Matrix:

| CO | PO1 | PO2 | PO3 | PO4 | PO5 |  |
|---|---|---|---|---|---|---|
| CO1 | ✔ | ✔ | ✔ |  |  |  |
| CO2 | ✔ | ✔ | ✔ | ✔ | ✔ |  |
| CO3 | ✔ | ✔ | ✔ |  |  |  |
| CO4 | ✔ | ✔ | ✔ |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |


| CO | PSO1 | PSO2 | PSO3 |  |
|---|---|---|---|---|
| CO1 | ✔ | ✔ |  |  |
| CO2 | ✔ | ✔ |  |  |
| CO3 | ✔ |  | ✔ |  |
| CO4 | ✔ |  |  |  |
|  |  |  |  |  |


APPENDIX: Detailed Course Content (Session-wise/ Module-wise) - Tentative

| Week | Module /
Topic | Description | Lectures |
|---|---|---|---|
| 1 | Introduction | Intro to autonomous systems, control, and robotics. Course overview and motivation. The first module will introduce the autonomous systems and their functions, operations, and application areas. It will also introduce control systems, a stream of engineering that studies how to control and analyse any engineering system. • Course introduction, Autonomous systems and Autonomous robots | 2 |
| 2–5 | System Dynamics | Transfer Function and state-space models, stability, MIMO, modeling of robots/quadrotors/AUVs. The behaviour of any engineering system can be understood using its dynamics. The process of obtaining the dynamics of a system is called modelling. In this module, we will learn how to represent the dynamical systems, such as a | 12 |


---
*Page Split*
---

| Week | Module /
Topic | Description | Lectures |
|---|---|---|---|
|  |  | robots and quadrotors with mathematical models, and analyse their stability. Specific topics include - • Transfer Functions (continuous and discrete-time systems) • State Space representation (continuous and discrete- time systems) • Nonlinear systems and their representation, • Equilibrium points and other relevant system properties • Multi-input, multi-output systems • Models of dynamical systems – quadrotors, AUVs |  |
| 6–9 | Feedback Control | PID, time/frequency analysis, state-feedback, LQR, tracking, compensators, inversion. The feedback control is continuously monitoring the performance of the controlled system and taking corrective actions if there is a deviation between desired and performed tasks. In this module, firstly, we will learn about how feedback control affects the dynamics, i.e. behaviour, of a system. Then, some well-known control techniques like Proportional- Derivative-Integral (PID) control and Linear quadratic (LQ) control will be studied. Specific topics include - • Time Domain Specifications • Frequency Domain Specifications • PID Control • State-feedback based control, LQR • Set-point tracking • Inversion-based Control | 12 |
| 10– 11 | Motion Planning | Dijkstra, A*, optimal and dynamic planning. Application to mobile robots/drones. Motion planning, also known as Path Planning, is an algorithm that describes the motion of a robot between two points and produces commands such that the robots have safe and optimal motion. In this module, techniques, and algorithms, such as Discrete planning, Optimal planning, and planning with dynamic constraints. Specific topics include - | 5 |


---
*Page Split*
---

| Week | Module /
Topic | Description | Lectures |
|---|---|---|---|
|  |  | • Djikstra’s Algorithm, A* algorithm and related related algorithms • Application to autonomous systems like mobile robots, quadrotors |  |
| 12– 13 | State Estimation | Kalman and Bayes filters, state uncertainty and estimation for control and planning. A robot’s control and motion planning are possible when its current state, i.e. position, speed and orientation, are known. Often these states of a robot are not available and require estimation. This module will teach state estimation techniques such as Kalman and Bayes filters. | 6 |
| 14– 15 | Localization & Mapping | SLAM, mapping unknown environments, localization in robots and quadrotors. An autonomous system often has to work in an unknown environment. SLAM is the computational technique of constructing or updating a map of an unknown environment while simultaneously keeping track of its location within it. This module will teach about Localization, Mapping, Simultaneous localization and mapping (SLAM) and their practical application in mobile robots and quadrotors. | 5 |


---
*Page Split*
---

Programme Outcomes (POs)

| PO
No. | Programme Outcomes |
|---|---|
| PO1 | Engineering knowledge: Apply the knowledge of mathematics, science, engineering fundamentals, and an engineering specialization to the solution of complex engineering problems. |
| PO2 | Problem analysis: Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions using first principles of mathematics, natural sciences, and engineering sciences |
| PO3 | Design/development of solutions: Design solutions for complex engineering problems and design system components or processes that meet the specified needs with appropriate consideration for the public health and safety, and the cultural, societal, and environmental considerations. |
| PO4 | Conduct investigations of complex problems: Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data, and synthesis of the information to provide valid conclusions. |
| PO5 | Modern tool usage: Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools including prediction and modeling to complex engineering activities with an understanding of the limitations. |
| PO6 | The engineer and society: Apply reasoning informed by the contextual knowledge to assess societal, health, safety, legal and cultural issues and the consequent responsibilities relevant to the professional engineering practice. |
| PO7 | Environment and sustainability: Understand the impact of the professional engineering solutions in societal and environmental contexts, and demonstrate the knowledge of, and need for sustainable development. |


---
*Page Split*
---

| PO8 | Ethics: Apply ethical principles and commit to professional ethics and
responsibilities and norms of the engineering practice. |
|---|---|
| PO9 | Individual and team work: Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings. |
| PO10 | Communication: Communicate effectively on complex engineering activities with the engineering community and with society at large, such as, being able to comprehend and write effective reports and design documentation, make effective presentations, and give and receive clear instructions. |
| PO11 | Project management and finance: Demonstrate knowledge and understanding of the engineering and management principles and apply these to one’s own work, as a member and leader in a team, to manage projects and in multidisciplinary environments. |
| PO12 | Life-long learning: Recognize the need for, and have the preparation and ability to engage in independent and life-long learning in the broadest context of technological change. |


Programme Specific Outcomes (PSOs)

| PSO
No. | Program Specific Outcomes (PSOs) |
|---|---|
| PSO1 | To apply the theoretical concepts of computer engineering and practical knowledge in analysis, design and development of computing systems and interdisciplinary applications. |
| PSO2 | Develop system solutions involving both hardware and software modules |
| PSO3 | To work as a socially responsible professional by applying ICT principles in real- world problems. |


---
*Page Split*
---



## Important Information

- **Course Code:** IE415
- **Course Title:** Control of Autonomous Systems
- **Document Source:** Course_Booklet_for_Autumn_2025-26.pdf
- **Category:** Academics (Intranet)
- **Scraped At:** 2026-06-01 07:56:43 UTC

## Related Links

- [DA-IICT Intranet Portal](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp)
- [Academic Guidelines](https://daiict.ac.in/academics)

## Downloadable Resources

| Resource | Type | Link |
|---|---|---|
| Course_Booklet_for_Autumn_2025-26.pdf | PDF | [Download Course_Booklet_for_Autumn_2025-26.pdf](https://intranet.daiict.ac.in/academics/Course_Booklet_for_Autumn_2025-26.pdf) |
