---
title: "DS614 Big Data Engineering Winter 2026"
url: "https://ecampus.daiict.ac.in/webapp/intranet/index.jsp"
category: "Academics - Course Policies"
scraped_by: "Squad D Scraper"
scraped_date: "2025-07-18"
team: "Squad D"
source_type: "PDF"
pdf_name: "DS614_BigDataEngineering_Winter26 - Ankush Chander.pdf"
course_code: "DS614"
semester: "Winter 2026"
---

# DS614: Big Data Engineering

## Course Overview

| Field | Details |
|---|---|
| **Course Code** | DS614 |
| **Course Name** | Big Data Engineering |
| **Instructor(s)** | Ankush Chander (Office: 3209, Faculty Block-3) |
| **Credits** | 3-0-2-4 (L-T-P-Cr) |
| **Semester Offered** | Winter 2026 |
| **Type** | Not explicitly stated (appears to be Core given program placement) |
| **Program(s)** | M.Sc Data Science |
| **Year / Semester in Program** | Semester III |
| **Associated Lab** | Integrated (2 practical hours per week as part of the 3-0-2-4 structure) |
| **Prerequisites** | None explicitly stated |
| **Foundation For** | None stated |

---

## Course Description

This course aims to equip students with a deep understanding of the architectural and theoretical foundations of big data systems, moving from storage internals (LSM-Trees, B-Trees) to modern Data Lakehouse architectures. It establishes a rigorous framework for distributed computing, examining replication, partitioning, and consistency models (CAP, PACELC) required for fault tolerance. Students will develop engineering proficiency in designing orchestrated batch and streaming pipelines while mastering probabilistic algorithms (HyperLogLog, Count-Min Sketch) for large-scale approximation. Finally, the course emphasizes reliability engineering, inculcating best practices for data quality, schema governance, and observability in production environments.

The course uses lab and project work to ensure the balance between theory and practice, ideas and their application.

---

## Course Outcomes (COs)

At the end of the course, students will be able to:

| CO | Description |
|---|---|
| CO1 | Analyze complex distributed storage requirements to select optimal data architectures (Lakehouse vs. Warehouse) based on trade-offs between consistency, availability, and latency. |
| CO2 | Design scalable data ingestion and orchestration systems that integrate batch and streaming data (Kafka/Airflow) to meet specified throughput and latency constraints. |
| CO3 | Apply mathematical principles of distributed computing and probabilistic algorithms (HyperLogLog, Count-Min Sketch) to solve large-scale cardinality and frequency estimation problems. |
| CO4 | Evaluate the impact of partitioning, replication, and concurrency control strategies on system fault tolerance and linearizability in distributed environments. |
| CO5 | Develop automated data governance and reliability mechanisms (schema contracts, observability) that address professional responsibilities regarding data quality and integrity. |

---

## Program Outcome Mapping (PO Mapping)

| PO1 | PO2 | PO3 | PO4 | PO5 | PO6 | PO7 | PO8 | PO9 | PO10 | PO11 | PO12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| X | X | X | | | | | | X | | | |

---

## Course Structure

| Unit | Topic | No. of Lectures |
|---|---|---|
| 1 | Introduction & Lifecycle: Data Engineering vs Data Science vs Software Eng. (1); The DE Lifecycle — Generation, Storage, Ingestion, Transformation, Serving (1) | 2 |
| 2 | Data storage: Data Structures of databases — Hash Indexes, LSM trees, B-trees (3); Architectures — Data Warehouse vs Data Lake vs Data Lakehouse (2); Table Formats — Bringing ACID to Data Lakes (Iceberg/Delta concepts) (1); Column-oriented Storage & Compression techniques (Parquet/ORC) (2) | 8 |
| 3 | Ingestion & Orchestration: Patterns — ETL vs ELT, Change Data Capture (CDC) (2); Stream Ingestion & Message Queues (Kafka theory — Topics, Partitions, Offsets) (2); Orchestration — Directed Acyclic Graphs (DAGs), Idempotency, and Scheduling (2); Encoding formats — Language-Specific Formats, JSON, XML, Binary variants, Protocol buffers, etc. (1) | 7 |
| 4 | Data Transformation: Data Modeling — Dimensional Modeling (Star/Snowflake) vs NoSQL patterns (2); Distributed Compute Models — MapReduce Paradigm vs DAG execution (Spark) (2); Streaming — Windowing, Watermarking, and State Management (2) | 6 |
| 5 | Reliability and Quality: Data Quality — Testing data, Circuit breakers, Data lineage (1); Observability — Monitoring pipelines, SLA/SLOs (1); Serving Layers — REST APIs vs High-throughput exports (1) | 3 |
| 6 | Distributed Systems Theory: Replication — Single-leader, Multi-leader, Quorums (2); Partitioning — Sharding strategies, Rebalancing, Consistent Hashing (2); Transactions — ACID, isolation levels, serializability (2); Fault-tolerant distributed systems (2) | 8 |
| 7 | Big data algorithms: Approximate Counting and Morris' Algorithm (2); Distinct Elements Problem — Count-Min Sketch (2); Large scale Linear Algebra — Dimensionality reduction (SVD/PCA via Power Iteration) (3) | 7 |
| **Total** | | **41** |

---

## Weekly Schedule / Lecture Plan

*Note: No weekly schedule with dates is available in the source document. Only a topic-wise lecture plan (Tentative Lecture Distribution) is provided above.*

---

## Evaluation / Grading Scheme

| Component | Weightage |
|---|---|
| Two Examinations (Mid-Sem and End-Sem) | 40% |
| Lab Submissions and Project Work | 60% |
| **Total** | **100%** |

---

## Textbooks and References

### Suggested Textbook(s) / References

1. Martin Kleppmann, *Designing Data-Intensive Applications*.
2. Joe Reis and Matt Housley, *Fundamentals of Data Engineering*.

### Reference Books

*None stated separately in source document.*

### Online Resources

*None stated in source document.*

---

## Program Structure Context

DS614 Big Data Engineering is offered to M.Sc Data Science Semester III students, with a 3-0-2-4 credit structure.

---

## Additional Notes

- The course places significant weight on lab and project work (60% of grade), emphasizing hands-on engineering of data pipelines (Kafka, Airflow, Spark) alongside theoretical foundations of distributed systems.
- Covers modern Data Lakehouse table formats (Iceberg/Delta) and probabilistic algorithms (HyperLogLog, Count-Min Sketch, Morris' Algorithm) not typically found in older big data course curricula.

---

## Downloads and Resources

| Resource | Type | Link |
|---|---|---|
| DS614_BigDataEngineering_Winter26 - Ankush Chander.pdf | PDF | [Download DS614_BigDataEngineering_Winter26 - Ankush Chander.pdf](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |

---

## Document Metadata

| Field | Value |
|---|---|
| **Source PDF** | DS614_BigDataEngineering_Winter26 - Ankush Chander.pdf |
| **Scraped Date** | 2025-07-18 |
| **Intranet Portal** | [DA-IICT Intranet](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |
| **Academic Guidelines** | [DAU Academics](https://daiict.ac.in/academics) |
