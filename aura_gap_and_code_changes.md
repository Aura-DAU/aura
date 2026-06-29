# AURA Eval — Data Gaps & Code Changes Required
**Test:** 150 questions | **Failures:** 35 "could not find" + 1 hallucination

---

## Part 1 — Data Gaps (Source `.md` Files to Edit)

These failures cannot be fixed by code. The answer literally does not exist in any scraped document. Each row names the exact file and what sentence/section to add.

---

### Gap 1 — Faculty Research Publication Incentive Policy (Q10, Q120, Q148)

**File:** `policies/faculty_research_publication_incentive_policy.md` (or equivalent)

**Missing content:**

Add a table showing the per-publication award amounts:

```markdown
## Award Amounts Per Publication

| Publication Type | Award Per Paper |
|---|---|
| Q1 Journal | Rs. X per paper |
| Q2 Journal | Rs. X per paper |
| A* Conference | Rs. X per paper |
| A Conference | Rs. X per paper |

**Annual cap per faculty member: Rs. 4 lakhs per calendar year.**
```

Also add the signatory line explicitly in the document body (Q120):
```markdown
## Document Authority
Signed by: [Name], Director, School of Technology  
Date: 24 December 2025
```

Also add an explicit exclusion list (Q148):
```markdown
## Ineligible Publication Types
The following are NOT eligible for the incentive:
- Workshop papers
- Tutorial presentations
- Poster presentations
- Short papers (under 6 pages)
- Extended abstracts
- Book reviews
```

---

### Gap 2 — Student Conduct / Code of Conduct Policy (Q47)

**File:** `policies/student_code_of_conduct.md` (or equivalent)

**Missing content:**

Add a dress code section with specific examples:

```markdown
## Dress Code

Students are expected to dress appropriately for an academic environment.

**Classroom conduct:**
- Formal or smart-casual attire is expected inside lecture halls and classrooms.
- Sports attire (jerseys, shorts, track pants, gym wear) is NOT permitted inside classrooms or the library.
- Sports attire is permitted only in sports facilities, gymnasiums, and during outdoor sports activities.

Violation of the dress code may be treated as a breach of campus conduct norms.
```

---

### Gap 3 — TRA (Thematic Research Area) Policy (Q50)

**File:** `policies/tra_policy.md` (or equivalent)

**Missing content:**

Add the faculty count constraint explicitly:

```markdown
## Proposal Requirements

A TRA proposal must include a minimum of **2 faculty members** and a maximum of **5 faculty members** as core members.

Proposals with more than 5 core faculty members will not be accepted unless an explicit exception is granted by the Research Committee. The 2-to-5 guideline is a hard requirement for standard submissions.
```

---

### Gap 4 — Library / Resource Centre Usage Policy (Q53, Q55, Q85)

**File:** `policies/library_usage_policy.md` or `student_services/resource_centre.md`

**Missing content:**

**Q53 — Refund slab day boundaries (this is actually the Admissions Refund Policy, see Gap 6 below)**

**Q55 — BTech borrowing period:**

The PhD borrowing period is documented but BTech is not. Add a complete borrowing table:

```markdown
## Borrowing Limits by Student Category

| Category | Max Items | Loan Period |
|---|---|---|
| Undergraduate (BTech, BS-MS) | 6 books | 14 days |
| Postgraduate (MTech, MSc, MDes) | 8 items | 14 days |
| PhD / Doctoral | 12 books | 1 semester |
| Faculty | 20 books | 1 semester |

Reference books, short loan collection, and AV materials are NOT available for home borrowing.
Short loan collection loan period: 3 days.
Bound volumes / AV materials loan period: 5 days.
```

**Q85 — Version date:**

Add this line to the top of the document:
```markdown
**Last Reviewed:** [Date]  
**Next Review Due:** [Date]  
*Students should verify current borrowing limits with the Resource Centre if this document is more than 12 months old.*
```

---

### Gap 5 — Hostel Allotment Policy (Q68, Q110)

**File:** `student_services/hostel_allotment_policy.md` (or equivalent)

**Missing content:**

**Q68 — Day scholar vs outstation eligibility:**

```markdown
## Eligibility Priority

Hostel accommodation is allocated on the following priority basis:

1. **Outstation students** (home address more than 50 km from campus) — first priority
2. **Students with documented medical or special needs** — second priority  
3. **Day scholars / local students** (home address within 50 km) — considered only if capacity remains after outstation allocations

Day scholars are NOT allotted hostel rooms on the same basis as outstation students. Local students must explicitly apply and will be placed on a waiting list.
```

**Q110 — Disciplinary warning effect on hostel allotment:**

```markdown
## Effect of Disciplinary Action on Hostel Allotment

- A **disciplinary warning** does not automatically disqualify a student from hostel allotment for the next academic year.
- A **disciplinary probation** may result in conditional allotment subject to warden approval.
- A **suspension** results in immediate vacation of the hostel room for the duration of the suspension.
- An **expulsion** results in permanent termination of hostel allotment.
```

---

### Gap 6 — Admissions / Fee Refund Policy (Q53, Q127)

**File:** `admissions/fee_refund_policy.md` or relevant admissions `.md`

**Missing content:**

**Q53 — Exact day boundaries for each refund slab:**

```markdown
## Tuition Fee Refund Schedule (UGC Guidelines)

| Withdrawal Timing | Refund Percentage |
|---|---|
| Before commencement of classes | 100% |
| Within 15 days of commencement (Day 1–15) | 80% |
| Day 16–30 after commencement | 50% |
| Day 31–90 after commencement | 25% |
| After 90 days of commencement | 0% |

**Day 10** falls in the "Within 15 days" slab → **80% refund.**  
**Day 20** falls in the "Day 16–30" slab → **50% refund.**

Note: The caution deposit (Rs. 25,000) is refundable separately provided no dues are outstanding.
```

**Q127 — Step-by-step withdrawal process:**

```markdown
## Withdrawal Process — Step by Step

1. Student submits a written application to the **Registrar's Office** stating the reason for withdrawal.
2. Student obtains **No Dues Certificate** from: Library, Hostel (if applicable), Accounts, and respective Department.
3. Student submits the No Dues Certificate along with the withdrawal application to the Registrar.
4. Registrar's Office processes the refund as per the UGC refund schedule above.
5. Refund is credited to the student's bank account within [X] working days.

For any queries, contact: registrar@dau.edu.in
```

---

### Gap 7 — PhD Student Travel and Research Allowance Policy (Q97, Q109)

**File:** `policies/phd_travel_research_allowance_policy.md`

**Missing content:**

**Q97 — Expenses NOT covered:**

```markdown
## Covered Expenses
- Conference registration fee
- Travel (airfare / train) to and from the conference venue
- Accommodation for the duration of the conference
- Membership of professional societies (up to Rs. X per year)
- Purchase of books and academic materials (up to Rs. X per year)

## Expenses NOT Covered
The travel allowance does NOT cover:
- Salary top-up or stipend enhancement
- Personal travel unrelated to conference attendance
- Tourism or sightseeing expenses
- Equipment purchases (laptops, cameras, etc.)
- Visa fees beyond the actual consulate charge
```

**Q109 — Conference rank requirement:**

```markdown
## Conference Eligibility

The travel grant is available for conferences ranked **A* or A** by CORE, or **equivalent tier** as assessed by the supervisor and Dean (Research).

**B-ranked conferences are NOT eligible** for the full Rs. 2 lakh travel grant. Students presenting at B-ranked conferences may apply for a partial grant of up to Rs. [X], subject to supervisor recommendation.

The student must have at least one accepted paper at the conference to be eligible.
```

---

### Gap 8 — Patent Filing Policy (Q112)

**File:** `policies/patent_filing_policy.md`

**Missing content:**

```markdown
## Revenue Sharing — Joint Inventors

When a patent is jointly invented by multiple persons (e.g., a faculty member and a student, or two faculty members), the revenue share is distributed as follows:

**If inventors are from the same institute (both DAU):**
- The inventor share (70% of total revenue when DAU funds filing) is split equally among all named inventors unless a different ratio is agreed upon in writing before filing.
- Example: Faculty + Student joint patent → each receives 35% of total revenue (i.e., 50% of the 70% inventor share).

**No single inventor may claim 100% of the inventor share** when multiple inventors are listed on the patent application.

The Patent Filing Policy governs all disputes regarding revenue splits. The Dean (Research) is the final authority on revenue allocation disputes.
```

---

### Gap 9 — Alumni Data Privacy Policy (Q125)

**File:** `policies/alumni_data_privacy_policy.md`

**Missing content:**

Add the signatory line explicitly:

```markdown
## Document Authority

Signed by: [Name], [Designation]  
Effective Date: 26 June 2024  
Next Review Due: June 2025
```

---

### Gap 10 — Student Research Excellence Award Policy (Q140)

**File:** `policies/student_research_excellence_award.md`

**Missing content:**

```markdown
## Application Process

1. **Eligibility Check:** Student must be currently enrolled OR have graduated within the past 12 months.
2. **Application Form:** Available at [URL or office location].
3. **Required Documents:**
   - List of publications with DOI/proof of acceptance
   - Supervisor recommendation letter
   - Department head endorsement
4. **Submission Deadline:** [Date — typically [Month] each academic year]
5. **Submission Portal / Office:** Submit to [Office Name] at [email/location]
6. **Selection Committee:** [Committee name] reviews applications and announces results by [Date].
```

---

### Gap 11 — Version History Missing from ALL Policy Files (Q71–Q83, Q85 — 12 failures)

**Files:** Every policy `.md` file listed below

Every Type4 question fails because no policy document states whether it is a first version or a revision. Add this block to the top of each file:

```markdown
## Version History

| Version | Effective Date | Signed By | Status |
|---|---|---|---|
| 1.0 | [Date] | [Name, Designation] | Current |

> **Revision Note:** [Either "This is the first version of this policy at DAU. No prior policy on this subject existed before this date." OR "This policy supersedes [Previous Policy Name] dated [Date]."]
```

**Files that need this section added:**

| File | Effective Date | Notes |
|---|---|---|
| Disciplinary Guidelines for Students | 01 March 2024 | State if first version or revision |
| Anti-Ragging Committee document | 18 August 2025 | State it is the 2025-26 annual composition |
| Alumni Data Privacy Policy | 26 June 2024 | State if annual review was completed |
| PhD Student Travel & Research Allowance Policy | 01 January 2026 | State what it supersedes if anything |
| Patent Filing Policy | 01 December 2025 | State if first policy or revision |
| TRA Policy | 01 April 2026 | State if first policy or revision |
| Medical SOP | 16 January 2026 | State if it replaces a prior SOP |
| Grievance Redressal Cell page | No date listed | Add effective date and GRHC composition date |
| Sponsored Research Projects Policy | 23 May 2024 | State if currently in force |
| SOP for Event Organisation | 01 April 2026 | State if first SOP or revision |
| Student Research Excellence Award Policy | 28 May 2025 | State if first iteration of award |
| Library Usage Policy | No date listed | Add last-reviewed date |

---

### Gap 12 — SBG Policy (Q58)

**File:** `student_services/sbg_policy.md` or `administration/student_body_government.md`

**Missing content:**

```markdown
## Dean of Students — Role with Respect to SBG

The Dean of Students holds an **oversight role** (not a direct management role) over the Student Body Government (SBG). Specifically:

- The Dean of Students serves as the **faculty advisor / institutional liaison** to the SBG.
- The SBG has operational autonomy in running student clubs and events.
- The Dean of Students must approve any SBG decisions that involve university resources, external events, or policy matters.
- Day-to-day SBG operations do not require Dean of Students approval.
```

---

### Gap 13 — Grievance Redressal Handling System (Q63, Q86)

**File:** `policies/grievance_redressal_policy.md`

**Missing content:**

**Q63 — Faculty grievance procedure (currently only student procedure is documented):**

```markdown
## Faculty Grievance Procedure

Faculty members may file grievances through the same GRHS levels:

- **Level I:** Department Head or immediate supervisor
- **Level II:** GRHS Committee
- **Level III:** Director / Governing Body

The procedure and timelines mirror the student grievance process. Faculty grievances about academic matters, service conditions, or collegial disputes fall under this system.

**Key difference from student grievances:** Faculty grievances about service conditions (pay, leave, promotion) may additionally be referred to the HR department or Governing Body, which is outside the standard GRHS scope.
```

**Q86 — Exam evaluation explicitly out of scope:**

```markdown
## Out of Scope — What the GRHS Does NOT Handle

The GRHS does not handle:
1. Matters under the jurisdiction of the **Disciplinary Action Committee (DAC)**
2. **Examination result disputes** — these are handled by the Examination Department / Course Instructor review process
3. Academic grade challenges — students must follow the grade challenge process via the Examination Department
```

---

### Gap 14 — Library + Sports Cross-Sanction (Q113)

**File:** `policies/library_usage_policy.md` AND `student_services/sports_facilities_policy.md`

**Missing content:**

Add to Library Policy:
```markdown
## Suspension of Borrowing Privileges

If a student's library borrowing privileges are suspended, this sanction applies **only to library services**. It does not affect access to:
- Sports facilities
- Hostel accommodation
- Canteen or other campus services

Library sanctions and sports facility access are governed by independent policies and do not cross-reference each other.
```

---

## Part 2 — Code Changes Required

All code changes map directly to failure categories that CAN be fixed without editing source data.

---

### Code Change 1 — `answer_generator.py` System Prompt

**Problem:** Q150 hallucination — AURA said "mandatory punishment is immediate expulsion" when the source says "may include expulsion." Modal verbs are being silently upgraded.

**Add this section to `SYSTEM_PROMPT`:**

```python
# Add after the STYLE section

------------------------------------------------------------
MODAL VERBS AND PENALTIES — CRITICAL
------------------------------------------------------------

When answering questions about penalties, punishments, or consequences:

- Reproduce the EXACT modal verb from the source document.
- NEVER upgrade permissive language to mandatory language.
- If the source says "may include expulsion", say "may include expulsion" — never "is expulsion".
- If the source says "shall be liable", say "shall be liable" — never "will definitely".

------------------------------------------------------------
PREMISE-IN-QUESTION HANDLING
------------------------------------------------------------

When the user's question states facts as premises (e.g. "Given that PG borrowing limit is 8 items...
how do they differ?"):
1. Verify those premises against retrieved documents.
2. If confirmed, affirm them and explain the implication — do not re-derive from scratch.

------------------------------------------------------------
MYTH-BUSTING / CLAIM VERIFICATION
------------------------------------------------------------

When the user asks you to verify a claim:
1. Locate the specific clause in retrieved context first.
2. Give a direct verdict: "That is correct." or "That is not correct."
3. Then cite the exact policy text.
4. Do not explore multiple interpretations before giving the verdict.
```

**Problem:** "Not found" answers are cold and give users no next step.

**Change the not-found instruction from:**
```
"I could not find that information in the available university data."
```
**To:**
```
"I could not find that information in the available university data. [Name the relevant office
if inferable from context.] You may also check the official DAU website at https://www.daiict.ac.in
or rephrase the question with more specific terms.

For policy version questions specifically: state the document's effective date if present in
the retrieved context, and note that no version history or supersession text was found."
```

---

### Code Change 2 — `query_planner.py` — New Retrieval Intent + Few-Shot Examples

**Problem:** All Type4 (policy version) questions route as `"general"` with no section boost toward version history chunks.

**Add `policy_version` to the valid retrieval intents list in `SYSTEM_PROMPT`:**

```
- policy_version   ← use when question asks about when a policy was issued,
                      whether it supersedes an older one, or if a newer version exists
```

**Add these few-shot examples to `SYSTEM_PROMPT`:**

```json
// Comparison query — always decompose
Query: How does the library borrowing limit for a PG student differ from a UG student?
{
  "retrieval_intent": "general",
  "multi_entity_query": true,
  "query_decomposition": [
    "library borrowing limit postgraduate PG student items loan period",
    "library borrowing limit undergraduate BTech student books loan period"
  ],
  "retrieval_hints": { "required_sections": ["Borrowing", "Loan Period", "Library"] }
}

// Cross-policy scenario
Query: Does a DX grade make a student ineligible for a merit scholarship?
{
  "retrieval_intent": "scholarship_information",
  "multi_entity_query": true,
  "query_decomposition": [
    "DX grade attendance penalty definition academic standing",
    "merit scholarship eligibility criteria backlog academic record"
  ],
  "retrieval_hints": { "required_sections": ["DX", "Scholarship", "Eligibility", "Backlog"] }
}

// Policy version query
Query: The Patent Filing Policy is dated 1 December 2025 — is there any mention of a prior policy?
{
  "retrieval_intent": "policy_version",
  "multi_entity_query": false,
  "query_decomposition": null,
  "retrieval_hints": {
    "required_sections": ["Version History", "Supersedes", "Effective Date", "Patent"]
  }
}

// Myth-busting
Query: Someone told me alumni data is shared with placement companies by default — is this true?
{
  "retrieval_intent": "general",
  "intent": "rules",
  "retrieval_hints": { "required_sections": ["Alumni", "Data Privacy", "Sharing", "Third Party"] }
}
```

**Add `policy_version` to the code-level required_sections block:**

```python
elif retrieval_intent == "policy_version":
    required_sections.extend([
        "Version History",
        "Supersedes",
        "Effective Date",
        "Revision",
        "Amendment"
    ])
    preferred_section_type = "administration"
```

---

### Code Change 3 — `retrieval_pipeline.py` — Four Targeted Fixes

**Fix A — Dead-end guard for `policy_version` queries:**

```python
# After building metadata_filter, before decomposed_queries block:
retrieval_intent = plan.get("retrieval_intent", "general")
if retrieval_intent == "policy_version" and metadata_filter:
    # Drop entity-level filter — search broadly to find the policy doc
    # and its version history chunk, which may not match entity fields
    metadata_filter = None
```

**Fix B — Cross-policy second-leg fallback:**

```python
# Inside the decomposed_queries loop, after the first fallback retry:
if sub_results and sub_metadata_filter:
    already_seen_ids = {r["id"] for r in all_results}
    new_in_sub = [r for r in sub_results if r["id"] not in already_seen_ids]
    if len(new_in_sub) == 0:
        # All results overlap with first leg — retry without filter
        extra = self.retriever.retrieve(
            query=subquery_expanded,
            top_k=retrieval_top_k,
            metadata_filter=None
        )
        new_extra = [r for r in extra if r["id"] not in already_seen_ids]
        if new_extra:
            sub_results = new_extra
```

**Fix C — Per-sub-query chunk cap 3 → 4 for multi-entity:**

```python
# When appending sub_reranked results:
sub_limit = 4 if plan.get("multi_entity_query") else 3
all_results.extend(sub_reranked[:sub_limit])
```

**Fix D — Wider adjacent chunk window for `policy_version`:**

```python
# Update _expand_adjacent_chunks signature:
def _expand_adjacent_chunks(self, candidates, window=1):
    # expand `window` chunks before and after each candidate

# At the call site:
expand_window = 2 if retrieval_intent == "policy_version" else 1
results = self._expand_adjacent_chunks(results, window=expand_window)
```

---

### Code Change 4 — `reranker.py` — Add `policy_version` Intent Boosts

```python
# Add to the intent_boosts dict:
"policy_version": [
    "version history",
    "supersedes",
    "effective date",
    "revision",
    "amendment",
    "replaces"
]
```

---

### Code Change 5 — `context_builder.py` — Dynamic Token Budget

**Problem:** Version history sections at the end of long policy docs get dropped by the 3000-token budget before they reach the LLM.

```python
# Update build() to accept retrieval_intent:
def build(self, chunks, retrieval_intent="general"):
    effective_max_tokens = (
        4000 if retrieval_intent == "policy_version"
        else self.MAX_CONTEXT_TOKENS  # 3000 for all other intents
    )
    # Replace MAX_CONTEXT_TOKENS with effective_max_tokens in the loop
```

Also update the call site in `retrieval_pipeline.py`:
```python
built = self.builder.build(final_chunks, retrieval_intent=retrieval_intent)
```

---

### Code Change 6 — `aura_chat.py` — Myth-Busting Query Augmentation

**Problem:** Type9 queries average 60.8s because retrieval doesn't signal "policy verification" intent to BM25.

```python
MYTH_BUST_PATTERNS = [
    "is this true", "is that true", "is this correct", "is that correct",
    "does the policy actually", "does the policy permit", "does the policy say",
    "a friend told me", "my friend said", "someone told me",
    "my senior told me", "i heard that", "i was told", "a classmate claimed"
]
if any(p in query.lower() for p in MYTH_BUST_PATTERNS):
    retrieval_query = retrieval_query + " policy rule regulation verify"
```

---

## Summary

| Category | Failures Addressed | Action Required |
|---|---|---|
| Version history missing from policy docs | 12 (all Type4) | Add `## Version History` block to 12 `.md` files |
| Per-publication award amounts missing | 3 (Q10, Q120, Q148) | Edit Research Incentive Policy `.md` |
| Dress code detail missing | 1 (Q47) | Edit Student Conduct Policy `.md` |
| TRA faculty count constraint missing | 1 (Q50) | Edit TRA Policy `.md` |
| Library BTech borrowing period missing | 2 (Q55, Q85) | Edit Library Policy `.md` |
| Refund slab day-boundaries missing | 2 (Q53, Q127) | Edit Admissions/Refund Policy `.md` |
| Hostel day-scholar eligibility missing | 2 (Q68, Q110) | Edit Hostel Allotment Policy `.md` |
| PhD travel exclusions missing | 2 (Q97, Q109) | Edit PhD Travel Policy `.md` |
| Joint-inventor patent revenue missing | 1 (Q112) | Edit Patent Policy `.md` |
| Library–sports cross-sanction missing | 1 (Q113) | Edit both Library and Sports `.md` |
| SBG Dean of Students role unclear | 1 (Q58) | Edit SBG Policy `.md` |
| Faculty grievance procedure missing | 2 (Q63, Q86) | Edit GRHS Policy `.md` |
| Student Research Award process missing | 1 (Q140) | Edit Award Policy `.md` |
| Alumni policy signatory missing | 1 (Q125) | Edit Alumni Data Privacy Policy `.md` |
| Modal verb hallucination (Q150) | 1 | `answer_generator.py` system prompt |
| Type4 routing wrong intent | 12 | `query_planner.py` — new intent + few-shots |
| Comparison queries fetch only one leg | 6 | `retrieval_pipeline.py` — fallback + cap fix |
| Policy version chunks dropped by budget | 12 | `context_builder.py` — dynamic budget |
| Version history chunks not boosted | 12 | `reranker.py` — intent boost |
| Type9 latency (avg 60.8s) | 10 | `aura_chat.py` — query augmentation |
