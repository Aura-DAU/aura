---
title: "EL203 - Embedded Hardware Design"
url: "https://intranet.daiict.ac.in/academics/EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf"
category: "Academics"
scraped_by: "Squad D Scraper"
scraped_date: "2026-06-01"
team: "Squad D"
source_type: "PDF"
pdf_name: "EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf"
---

# EL203 - Embedded Hardware Design

## Overview

This document presents the detailed policy and syllabus structure for the course Embedded Hardware Design (EL203). It includes details on course objectives, credits, prerequisites, syllabus content, evaluation schemes, and contact information where available.

## Main Content

| Course Title | Embedded Hardware Design |  |  |
|---|---|---|---|
| Course Code | EL203 | Credit Structure | 3-0-2-4 (L-T-P-C) |
| Category | Core | Semester | Winter Semester (AY 25-26) |
| Program | B.Tech. (ICT, CS, EnV) |  |  |
| Prerequisites | Digital Logic and Computer Organization |  |  |
| Course
Objectives/
Brief Course
Description | This course will give the students an introductory understanding of embedded
systems which includes the programming the AVR microcontroller/ARM processor
based Microcontrollers, VHDL, Hardware/Software Co-Design, interfacing of
external peripheral devices to microcontroller, and troubleshooting the embedded
systems (PO1, PO3, PSO1). The course consists of two parts which are (i) interactive
lecture section and (ii) hand-on which will provide a platform to develop an
embedded system from scratch (PO11, PEO1, PEO2). Students will gain knowledge
on embedded system functions, embedded components, embedded software, and
coding which are required for practical implementation of a real embedded system
(PO5, PO9, PSO2, PEO5). Students will acquire skills on embedded system coding,
microcontrollers, sensors, and actuators to become a good embedded system engineer
(PSO2, PEO3). Today, world leading companies are looking for the people who are
expertise in the areas of embedded systems, embedded AI, and edge computing, etc
(PO10, PO11). This course will provide a platform to develop skills for which
companies are interested to hire professionals (PO6). |  |  |
| Evaluation/
Grading Policy | Two in-semester examinations, a final examination, and lab assignments.
Evaluation scheme: (i) First In-Sem Exam: 20%, (ii) Second In-Sem Exam: 20%,
(iii) End-Sem Exam: 30%, and (iv) Labs: 30%. |  |  |
| Course
Materials/
References | Text Book: Frank Vahid and Tony Givargis, Embedded System Design: A Unified
Hardware/Software Introduction, Wiley, Student edition, 2006.
Reference Book:
1) Sarah Harris and David Harris, Digital Design and Computer Architecture:
ARM Edition, Morgan Kaufmann Publishers Inc., United States, May 2015.
2) Jonathan Walker Valvano, Embedded Systems: Introduction to Arm®
Cortex™-M Microcontrollers, 5th Edition, CreateSpace Independent Publishing
Platform, 2011.
3) Samir Palnitkar, Digital Design using Verilog HDL, Prentice Hall; 2nd Edition,
2003.
4) ARM System Developer’s Guide: Designing and Optimizing System Software
1st Edition (Designing and Optimizing System Software) Publisher: Morgan
Kaufmann Publishers Inc., 2011. |  |  |
| Detailed Course
Content | APPENDIX |  |  |


---
*Page Split*
---

| Course Outcome: |  |  |
|---|---|---|
| The Course Outcomes (COs) are mapped to the course modules, identified as CO1, CO2, CO3, CO4, |  |  |
| CO5, CO6, and CO7. The course weightage is distributed based on no. of lectures. The expected POs |  |  |
| versus COs matrices are tabulated below. |  |  |
| POs-COs Matrix: |  |  |
| Mapping of Course Outcomes (COs) and Program Outcomes (POs)
Note: 1 = Slight 2 = Moderate 3 = STRONG
Course Program Outcomes (POs) PSOs
Modules Hours
Outcomes PO1 PO2 PO3 PO4 PO5 PO6 PO7 PO8 PO9 PO10 PO11 PO12 PSO1 PSO2 PSO3
CO1 1 4 1 3 3 3 2 0 0 0 0 0 0 2 2 0 3
CO2 2 13 0 3 3 3 0 2 0 0 0 0 0 0 2 2 3
CO3 3 12 0 3 3 3 2 2 1 0 0 2 2 2 2 2 3
CO4 4 9 0 3 3 3 0 2 0 0 0 2 2 2 2 2 3
CO5 5 8 0 3 3 0 0 0 0 1 1 0 0 0 2 0 3
CO6 6 7 0 3 3 3 2 0 0 0 0 0 0 0 2 0 3
CO7 7 9 0 3 3 0 0 0 0 0 0 0 0 0 3 0 3
AVG 0.14 3.00 3.00 2.14 0.86 0.86 0.14 0.14 0.14 0.57 0.57 0.86 2.14 0.86 3.00 |  |  |
| Course
Outcomes | Modules | Hours |
| CO1 | 1 | 4 |
| CO2 | 2 | 13 |
| CO3 | 3 | 12 |
| CO4 | 4 | 9 |
| CO5 | 5 | 8 |
| CO6 | 6 | 7 |
| CO7
AVG | 7 | 9 |


APPENDIX: Detailed Course Content

| Sl. No | Description |  | No. of
Lectures |
|---|---|---|---|
| Module-1 | Introduction |  | 4 |
|  | 1.1 | Embedded Systems Overview | 1 |
|  | 1.2 | Design Challenges – Optimizing Design Metrics | 1 |
|  | 1.3 | Processor and IC Technologies | 1 |
|  | 1.4 | Design Technology and Trade-offs | 1 |
| Module-2 | Custom Single-Purpose Processors |  | 13 |
|  | 2.1 | Binary Information Implemented with MOS transistors | 1 |
|  | 2.2 | Digital Logic, Logic gates | 1 |
|  | 2.3 | Combinational and Sequential Logic | 2 |
|  | 2.4 | RT-Level Combinational and Sequential Components | 1 |
|  | 2.5 | Basic Computer Architecture | 1 |
|  | 2.6 | Finite State Machines (FSM) | 2 |
|  | 2.7 | Optimizing Datapath | 2 |
|  | 2.8 | Hardware Description Languages: Verilog HDL | 2 |
|  | 2.9 | Field Programmable Gate Array (FPGA) | 1 |
| Module-3 | Microcontroller Based on Cortex-M Class Processors/AVR
microcontroller |  | 12 |
|  | 3.1 | AVR microcontroller, ARM/Cortex family
microcontrollers | 1 |
|  | 3.2 | AVR microcontroller, ARM Assembly Language | 3 |
|  | 3.3 | Introduction to Embedded C | 1 |
|  | 3.4 | Mixing C and Assembly | 1 |
|  | 3.5 | Developing programs with ARM/Cortex
microcontrollers | 3 |
|  | 3.6 | Peripheral Drivers Development | 2 |
|  | 3.7 | Introduction to Keil µVision | 1 |
| Module-4 | Real-Time Interfacing |  | 9 |
|  | 4.1 | Introduction to Input/Output | 1 |
|  | 4.2 | SysTick Timer | 1 |
|  | 4.3 | ARM interrupts and interrupt processing | 1 |


---
*Page Split*
---

|  | 4.4 | GPIO Polling and Interrupt | 1 |
|---|---|---|---|
|  | 4.5 | UART-Serial Interface | 1 |
|  | 4.6 | Analog I/O Interfacing, I/O Synchronization, RS232,
I2C, CAN | 2 |
|  | 4.7 | USB Protocols, Bluetooth | 2 |
| Module-5 | Implementation of Embedded Systems |  | 8 |
|  | 5.1 | Open-Loop and Closed-Loop Control Systems | 1 |
|  | 5.2 | Example: Self-Driving Car | 1 |
|  | 5.3 | ADC and DAC | 1 |
|  | 5.4 | IMU (Inertial Measurement Unit), Image Sensor,
Pressure Sensor | 2 |
|  | 5.5 | Servo-Motor, Pulse-Width-Modulation (PWM) | 1 |
|  | 5.6 | Proportional-Integral-Derivative (PID) Controller | 1 |
|  | 5.7 | Integration of Sensors and Motors with
RaspberryPi/Arduino Boards | 1 |
| Module-6 | Memory |  | 7 |
|  | 6.1 | Introduction | 1 |
|  | 6.2 | Common Memory Types, ROM, RAM, EEPROM,
SRAM | 3 |
|  | 6.3 | Memory Hierarchy and Cache | 1 |
|  | 6.4 | Advanced RAM, DRAM | 1 |
|  | 6.5 | Memory Management | 1 |
| Module-7 | IC Technology |  | 9 |
|  | 7.1 | Full-Custom IC Technology | 2 |
|  | 7.2 | Semi-Custom IC Technology | 2 |
|  | 7.3 | Programmable Logic Device IC Technology | 1 |
|  | 7.4 | Design Technology: Automation and Synthesis | 2 |
|  | 7.5 | Verification: Hardware/Software Co-Simulation | 2 |


## Important Information

- **Course Code:** EL203
- **Course Title:** Embedded Hardware Design
- **Document Source:** EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf
- **Category:** Academics (Intranet)
- **Scraped At:** 2026-06-01 07:38:57 UTC

## Related Links

- [DA-IICT Intranet Portal](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp)
- [Academic Guidelines](https://daiict.ac.in/academics)

## Downloadable Resources

| Resource | Type | Link |
|---|---|---|
| EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf | PDF | [Download EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf](https://intranet.daiict.ac.in/academics/EL203_EmbeddedHardwareDesign_Winter26 - Tapas Kumar Maiti.pdf) |
