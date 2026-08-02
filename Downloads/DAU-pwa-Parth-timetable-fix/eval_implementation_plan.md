# RAG Detailed Report: Implementation Audit & Plan

Based on a thorough review of the `rag_detailed_report.md` (which documents 170 Q&A benchmark failures) and a complete audit of the codebase, I have distilled the failures into 7 core architectural issues. 

Below is the Implementation Audit detailing the status of each issue, followed by the Implementation Plan.

---

## Implementation Audit

### 1. Auth/Session Gating Bug
**Intended Behavior**: General policy and curriculum questions (e.g., minimum CPI, exam duration) must bypass the strict user-profile requirement and fall back to general document search when the user context is missing.
**Current Implementation**: 
- `server/rag/personal_query_classifier.py` defines a `PUBLIC_PROGRAMME_OVERRIDE_PAT` to prevent public curriculum queries from being misclassified as personal.
- `server/rag/pipeline/retrieval/retrieval_pipeline.py` (lines 480-538) correctly checks `_EXPLICIT_PROGRAMME_IN_QUERY_RE` to bypass the `ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE` for general queries.
**Status**: ✅ Fully Implemented
**Reasoning**: Recent commits to `retrieval_pipeline.py` and `personal_query_classifier.py` have fully resolved this bug.

### 2. Lack of Temporal Awareness on Static Data
**Intended Behavior**: The system must decline time-relative queries (e.g., "currently open", "upcoming") against static archives, or at least warn the user if it is using outdated rules.
**Current Implementation**: 
- `server/rag/pipeline/generation/answer_generator.py` includes a "Document Recency Warning" prompt directive. The LLM is instructed to prefix its answer with a caveat if the retrieved `rule_year` is 2025-26 or older.
**Status**: 🟠 Implemented Differently
**Reasoning**: Instead of live API cross-checking (which is complex for static document corpora), the system gracefully warns the user that the information might be outdated, fulfilling the requirement safely.

### 3. Missing Course Code <-> Title Resolution
**Intended Behavior**: Users ask for course names ("Machine Learning"), but the timetable data only uses codes ("IT206"). The system needs a way to map these so timetable queries don't fail.
**Current Implementation**: The timetable `service.py` supports a `course_name` field, but there is no global dictionary or query rewriting logic in `query_planner.py` to map natural language course names to their exact codes before retrieval.
**Status**: ❌ Missing
**Reasoning**: The system cannot consistently bridge the gap between semantic names and rigid timetable codes.

### 4. Poor Scatter-Gather Retrieval (Faculty & Directories)
**Intended Behavior**: The system must be able to aggregate lists (e.g., "all faculty doing NLP", "all dormant clubs") without relying purely on top-K semantic search, which truncates the list.
**Current Implementation**: `server/rag/pipeline/ingestion/chunking/metadata_extractors.py` has basic metadata extraction, but it does not formally extract and tag "Research Domain" or "Club Status" for structured filtering.
**Status**: ❌ Missing
**Reasoning**: RAG pipelines notoriously struggle with aggregation. Without structured metadata tagging for research domains, scatter-gather queries will continue to fail.

### 5. Table and Policy Chunking Fragmentation
**Intended Behavior**: Nuanced rules in complex tables (e.g., fee structures, admission criteria) must not be fractured across chunks, causing the LLM to miss exceptions.
**Current Implementation**: The ingestion pipeline (`chunker.py` and `process_corpus.py`) chunks by standard delimiters and headers, but lacks semantic grouping for multi-row tables or hierarchical policies.
**Status**: ❌ Missing
**Reasoning**: The current chunking strategy breaks apart contextual tables, leading to incomplete retrieval.

### 6. Weak Grounding on Subjective/Reasoning Prompts
**Intended Behavior**: The LLM must decline ranking or subjective synthesis (e.g., "best club", "optimal roadmap") if explicit facts are absent, rather than hallucinating attributes.
**Current Implementation**: The `answer_generator.py` lacks strict anti-synthesis instructions.
**Status**: ❌ Missing
**Reasoning**: The system prompt needs hardening to reject subjective ungrounded synthesis.

### 7. Adversarial Hallucination Vulnerability
**Intended Behavior**: The bot must decline to answer trap questions (e.g., "Nobel Prize winners at DAU") rather than guessing.
**Current Implementation**: The LLM attempts to answer based on vague semantic matches rather than relying on exact entity verification.
**Status**: ❌ Missing
**Reasoning**: Requires strengthening the "I don't know" threshold in `answer_generator.py`.

---

## Implementation Plan

### Already Implemented
1. **Auth/Session Gating Bug**: Fixed via `PUBLIC_PROGRAMME_OVERRIDE_PAT` in `retrieval_pipeline.py`. No further work needed.
2. **Temporal Awareness**: Fixed via the "Document Recency Warning" in `answer_generator.py`. No further work needed.

### Needs Implementation

#### 1. Course Code <-> Title Resolution
**File(s)**: `server/rag/pipeline/retrieval/query_planner.py`
**Current behavior**: Natural language course names are passed directly to retrieval, failing to match timetable codes.
**Required changes**: Implement a lookup dictionary (or a pre-retrieval LLM prompt step) to translate semantic course names to exact codes before executing the timetable tool.
**Reasoning**: Timetable data is strictly keyed by code.
**Estimated complexity**: Medium

#### 2. Faculty Metadata Tagging (Scatter-Gather)
**File(s)**: `server/rag/pipeline/ingestion/chunking/metadata_extractors.py`, `server/rag/pipeline/retrieval/retrieval_pipeline.py`
**Current behavior**: Faculty profiles are chunked as raw text; research domains aren't extracted as filterable metadata.
**Required changes**: Add a `research_domain` metadata extractor for faculty profiles. Update the query planner to emit `research_domain` filters for directory questions.
**Reasoning**: Enables exact-match filtering for aggregation queries.
**Estimated complexity**: Medium

#### 3. Strict Fact-Grounding & Anti-Hallucination
**File(s)**: `server/rag/pipeline/generation/answer_generator.py`
**Current behavior**: The LLM synthesizes roadmaps and hallucinates non-existent entities.
**Required changes**: Update the system prompt with strict directives:
- "Decline to rank or synthesize subjective roadmaps (e.g. 'best club') unless explicitly documented."
- "If asked about a specific named entity (e.g., 'Head of Department', 'Google I/O'), verify it exists in the provided context. If absent, explicitly state the entity is not documented."
**Reasoning**: Prevents the LLM from trying to be "helpful" by guessing.
**Estimated complexity**: Low

### Optional Improvements
- **Semantic Table Chunking** (OPTIONAL): Refactor `chunker.py` to detect Markdown tables and keep them intact within a single chunk, even if it slightly exceeds the token limit. This would resolve the Table Fragmentation issue (Issue 5), but requires significant changes to the ingestion pipeline.

## User Review Required
> [!IMPORTANT]
> The scatter-gather issue (Issue 4) and Table Chunking issue (Issue 5) require re-running the entire ingestion pipeline to apply new metadata and chunking rules. Are you comfortable with me writing the code for these, and you handling the ingestion script later? 
> 
> Please approve this plan, and I will begin implementing the missing features.
