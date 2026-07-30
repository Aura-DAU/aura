---
title: "IT594 Deep Neural NLP & Applications Autumn Semester 2026-27"
document_year: "2026-27"
url: "https://ecampus.daiict.ac.in/webapp/intranet/index.jsp"
category: "Academics - Course Policies"
scraped_by: "Squad D Scraper"
scraped_date: "2026-07-23"
team: "Squad D"
source_type: "PDF"
pdf_name: "IT594__2026-27__IT594_DeepNeuralNLP&Applications - Sourish Dasgupta.pdf"
course_code: "IT594"
semester: "Autumn Semester 2026-27"
authorization: ["student", "faculty"]
---

# IT594: Deep Neural NLP & Applications

## Course Overview

| Field | Details |
|---|---|
| **Course Code** | IT594 |
| **Course Name** | Deep Neural NLP & Applications |
| **Instructor(s)** | Sourish Dasgupta |
| **Credits** | 3-0-2-4 (L-T-P-Cr) |
| **Semester Offered** | Autumn Semester (AY 2026-27) |
| **Type** | Technical Elective / ML Specialization Elective |
| **Program(s)** | M.Tech. III / M.Sc. Data Science III / B.Tech. VII Semester |
| **Year / Semester in Program** | Semester III (M.Tech./M.Sc.) or Semester VII (B.Tech.) |
| **Associated Lab** | Yes - project studio, guided implementation, and system evaluation |
| **Prerequisites** | Programming in Python; basic linear algebra and probability. Prior exposure to machine learning is helpful but not mandatory |
| **Foundation For** | None stated |

Lectures: Yes (offline). TA Contact Information: TBD.

---

## Course Description

This course is designed for students who intend to work as NLP research engineers, applied scientists, or researchers. It develops a rigorous understanding of how language is represented, modelled, learned, generated, grounded, and evaluated - from classical NLP formalisms to contextual neural representations, Transformers, pretrained language models, retrieval- and tool-augmented systems, and reliability-aware deployment. The course is organized as a cumulative representational journey: each new mechanism is introduced only after the limitations of the preceding approach become clear.

The course combines mathematical and linguistic foundations with implementation, experimentation, and critical evaluation. Students will build an end-to-end NLP system through staged project milestones and will be expected to justify design choices, diagnose failure modes, and make evidence-bounded claims.

**Course Structure (as stated in source):**
- Lectures: Conceptual and mathematical foundations, classical-to-neural continuity, architecture, learning objectives, and model limitations.
- Practical sessions: Guided implementation using Python and contemporary open-source NLP and deep-learning libraries.
- Project spine: A semester-long group project developed through representation, modelling, adaptation, grounding, and evaluation milestones.
- Scientific practice: Reproducible baselines, ablations, error analysis, uncertainty reporting, and responsible deployment considerations.

**Pedagogical Principle (as stated in source):** Each module follows the same progression: What is the object or mechanism? Why is it needed? Why does the preceding intuitive solution fail? What remains unresolved? The course therefore treats modern NLP not as a catalogue of models, but as a connected sequence of representational and computational choices whose benefits and limitations must be interpreted, implemented, and evaluated.

---

## Course Outcomes (COs)

**General outcomes (as stated in source):**

| CO | Description |
|---|---|
| CO1 | Explain the representational progression from strings, grammars, and formal semantics to sparse, dense, and contextual neural representations |
| CO2 | Derive and interpret the principal mathematical operations underlying text representations, recurrent models, attention, Transformers, and adaptation methods |
| CO3 | Select and justify tokenization, representation, architecture, training, retrieval, decoding, and evaluation choices for a specified NLP problem |
| CO4 | Implement and compare classical, neural, Transformer-based, and retrieval- or tool-augmented baselines |
| CO5 | Diagnose failures arising from data, representation, optimization, retrieval, generation, evaluation, and distribution shift |
| CO6 | Design evaluation protocols covering task performance, uncertainty, factuality, robustness, and relevant fairness, privacy, and deployment risks |
| CO7 | Deliver and defend an end-to-end NLP system through reproducible experiments and evidence-bounded conclusions |

**NAAC Compliant Course Outcome (as stated in source)** — after successful completion of the course, the student will have the ability to:

| CO | Description |
|---|---|
| NAAC-CO1 | Complete an end-to-end real-life industry-level NLP project (P1, P2, P3, P4, P5) |
| NAAC-CO2 | Thoroughly understand the fundamentals of key paradigms of classical NLP - their pros and cons (P1, P2, P3, P4, P5, P12) |
| NAAC-CO3 | Thoroughly understand how the foundational concepts of classical NLP apply to modern deep learning-based NLP (P1, P2, P3, P4, P5) |
| NAAC-CO4 | Design and implement industry-standard NLP systems (P1, P2, P3, P4, P5, P9) |
| NAAC-CO5 | Thoroughly understand industry-standard NLP libraries (P1, P2, P3, P4, P5) |

---

## Program Outcome Mapping (PO Mapping)

| PO1 | PO2 | PO3 | PO4 | PO5 | PO6 | PO7 | PO8 | PO9 | PO10 | PO11 | PO12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| X | X | X | X | X | | | | X | | | X |

---

## Course Structure

*Core lectures: 40. Two additional contact sessions are reserved for project design/review and final demonstrations, giving 42 scheduled sessions in total.*

| Unit | Topic | No. of Lectures |
|---|---|---|
| Module 0: Classical NLP and the Representational Problem | Central question: How did NLP represent language before vector-space learning, and why did vectors become necessary? Language as a machine-representable object; preservation, forgetting, and task dependence. Exact strings, regular expressions, finite-state recognizers and transducers; practical limits of surface patterns. Phrase-structure grammars, CFGs, constituency and dependency syntax, parsing, hierarchy, recursion, and ambiguity. Fregean compositionality; Montague-style formal semantics; predicates, roles, quantifiers, scope, and lambda-calculus composition. Pragmatics, uncertainty, probabilistic NLP, and the transition from explicit symbolic structures to learned vector representations | 5 |
| Module 1: Linguistic Units in Vector Worlds | Central question: What does it mean to place linguistic units in a vector space? Raw text, Unicode, normalization, tokenization, words, morphemes, characters, and subword units. BPE, WordPiece, unigram tokenization, vocabulary-size trade-offs, multilingual and social consequences. One-hot vectors, standard basis, lexical "word-ness," binary/count vectors, n-grams, and document-term matrices. TF-IDF, length normalization, lexical weighting, and interpretable sparse baselines. Norms, Euclidean and Manhattan distance, dot product, cosine, Jaccard, edit distance, Mahalanobis distance, and when each is inappropriate. Linear maps, strict change of basis versus learned representation maps, row and column interpretations, rank, and learned geometry. Null space, row space, column space, left null space, invariance, erased distinctions, and unreachable directions. Distributional context matrices, PMI/PPMI, SVD, CBOW, skip-gram, negative sampling, GloVe, static embeddings, polysemy, anisotropy, and the need for contextual representations | 8 |
| Module 2: Neural Computation over Language Sequences | Central question: How can a neural model compute a representation from a variable-length sequence? Affine maps, nonlinear activations, hidden layers, softmax, cross-entropy, and backpropagation as learned feature construction. Fixed context windows, feed-forward neural language models, one-dimensional convolution, pooling, and local pattern detectors. Recurrent neural networks, state as accumulated memory, unfolding through time, bidirectionality, and backpropagation through time. Vanishing/exploding gradients, distant dependencies, state bottlenecks, LSTM and GRU gating as controlled information flow. Encoder-decoder sequence models, teacher forcing, sequence likelihood, exposure bias, and the fixed-vector bottleneck | 5 |
| Module 3: Attention and Transformers | Central question: Why attention, and how does a Transformer compute contextual representations? Alignment in sequence-to-sequence models and attention as direct access to relevant source states. Queries, keys, and values; additive and dot-product attention; comparison, normalization, and weighted mixing. Scaled dot-product attention, masking, and the limits of interpreting attention weights as causal explanations. Self-attention, contextualization, multi-head attention, and multiple learned relational views. Position information: absolute, sinusoidal, relative, and rotary encodings at an introductory level. Transformer blocks: residual connections, layer normalization, feed-forward sublayers, and repeated representation refinement. Encoder-only, decoder-only, and encoder-decoder architectures; computational complexity, long-context limitations, and efficient-attention ideas | 7 |
| Module 4: Language Modelling, Pretraining, and Adaptation | Central question: How does a Transformer acquire general language capabilities and become useful for a task? Autoregressive factorization; causal, masked, denoising, and span-corruption objectives; objective-architecture interaction. What pretraining can learn: linguistic regularities, corpus-reflected knowledge, memorization, bias, duplication, and contamination. Prompting, demonstrations, in-context learning, prompt sensitivity, supervised fine-tuning, and decoding choices. Parameter-efficient adaptation: adapters, prompt/prefix tuning, LoRA, low-rank updates, and their interpretive limits. Preference alignment: reward models, RLHF, direct preference optimization, specification limits, reward hacking, and overoptimization | 5 |
| Module 5: Retrieval, Grounding, Tools, and Controlled Generation | Central question: When should a model consult external evidence, computation, or formal constraints? Sparse and dense retrieval, bi-encoders, cross-encoders, reranking, hybrid retrieval, and retrieval evaluation. Retrieval-augmented generation: chunking, indexing, retrieval, context construction, evidence use, citation, and failure decomposition. Tool and function calling: schema-based actions, calculators, search, databases, code execution, result integration, and verification. Regex-, schema-, and grammar-constrained generation; syntactic validity versus semantic correctness; basic agent loops, memory, permissions, and error compounding | 4 |
| Module 6: Core NLP Tasks as Modelling Problems | Central question: How do task definitions determine representation, output structure, loss, and evaluation? Classification and multilabel prediction; sequence labelling, NER, span extraction, relation and event extraction. Dependency parsing, semantic parsing, natural-language inference, question answering, and retrieval-versus-reading formulations. Conditional generation: translation, summarization, simplification, dialogue, and task-conditioned norms of preservation, deletion, abstraction, and generation | 3 |
| Module 7: Evaluation, Reliability, and Responsible NLP | Central question: What evidence is sufficient to claim that an NLP system works and can be trusted? Evaluation design: train/development/test separation, leakage, distribution shift, uncertainty, confidence intervals, ablations, and error analysis. Metrics as operational definitions; human evaluation; LLM-as-judge; calibration, abstention, risk-coverage, hallucination, factuality, and robustness. Bias, fairness, privacy, memorization, data governance, model/data documentation, monitoring, human oversight, appeal, incident response, and when not to automate | 3 |
| **Total** | | **40** |

---

## Weekly Schedule / Lecture Plan

*Note: No dated weekly schedule is available; instead, the course follows a semester-long project spine tied to modules, as follows:*

| Stage | Required Project Evidence |
|---|---|
| After Module 0 | Define the task, users, linguistic units, task norm, desired distinctions, and failure taxonomy |
| After Module 1 | Build sparse and dense representation baselines; justify tokenization and similarity choices |
| After Module 2 | Build a neural sequence baseline and diagnose information-flow limitations |
| After Module 3 | Implement or adapt a Transformer model; compare architecture and efficiency trade-offs |
| After Module 4 | Prompt, fine-tune, or parameter-efficiently adapt a pretrained model; analyse decoding and behaviour |
| After Module 5 | Add retrieval, tools, or output constraints only where the task justifies them |
| After Module 6 | Specify task-conditioned success criteria and compare suitable baselines |
| After Module 7 | Conduct reliability, uncertainty, robustness, fairness/privacy, and deployment analysis |

---

## Evaluation / Grading Scheme

| Component | Weightage |
|---|---|
| Mid-semester Examination | 25% |
| End-semester Examination | 35% |
| Project Milestone 1: Representation and Baselines | 5% |
| Project Milestone 2: Neural / Transformer Model | 5% |
| Project Milestone 3: Adaptation, Grounding, or Controlled Generation | 5% |
| Project Milestone 4: Evaluation and Failure-Analysis Report | 5% |
| Final Demonstration and Individual Defence | 10% |
| **Total** | **100%** |

**Project policy**: Group size will be at most four students. Individual understanding will be assessed through milestone reviews (which include lab assignment performance) and the final defence.

**Grading Policy**: For Credit — AA: ≥85%; AB: ≥75%; BB: ≥65%; BC: ≥55%; CC: ≥45%; CD: ≥35%; DD: ≥25%; F: <25%. For Audit — Pass: ≥25%.

---

## Textbooks and References

### Reference Books

1. Daniel Jurafsky and James H. Martin, *Speech and Language Processing*.
2. Jacob Eisenstein, *Introduction to Natural Language Processing*.
3. Yoav Goldberg, *Neural Network Methods for Natural Language Processing*, and *A Primer on Neural Network Models for NLP*.
4. Lewis Tunstall, Leandro von Werra, and Thomas Wolf, *Natural Language Processing with Transformers*.
5. Selected research papers and technical documentation announced module-wise.

### Online Resources

None stated in source document.

---

## Program Structure Context

IT594 is a Technical Elective / ML Specialization Elective for M.Tech. III / M.Sc. Data Science III / B.Tech. VII Semester students, offered in the Autumn Semester (AY 2026-27).

---

## Additional Notes

**Implementation environment (as stated in source)**: Python, PyTorch, Hugging Face Transformers/Datasets, spaCy, scikit-learn, and supporting evaluation and retrieval libraries. The exact software stack may evolve; conceptual competence is primary.

---

## Downloads and Resources

| Resource | Type | Link |
|---|---|---|
| IT594__2026-27__IT594_DeepNeuralNLP&Applications - Sourish Dasgupta.pdf | PDF | [Download PDF]({ORIGINAL_URL}) |

---

## Document Metadata

| Field | Value |
|---|---|
| **Source PDF** | IT594__2026-27__IT594_DeepNeuralNLP&Applications - Sourish Dasgupta.pdf |
| **Scraped Date** | 2026-07-23 |
| **Intranet Portal** | [DA-IICT Intranet](https://ecampus.daiict.ac.in/webapp/intranet/index.jsp) |
| **Academic Guidelines** | [DAU Academics](https://daiict.ac.in/academics) |
