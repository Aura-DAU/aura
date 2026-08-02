# 03 — Database Schema

## Two completely separate databases — this is non-negotiable

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│  AURA Auth DB (PostgreSQL)       │     │  DAU ERP DB (existing, read-only) │
│  Lives on AURA's own server       │     │  AURA never writes to this         │
│  Owned by the AURA team           │     │  AURA gets a read-only DB user     │
│                                   │     │  with restricted table access      │
│  - users                          │     │                                    │
│  - sessions                       │     │  - students (roll, name, dept...)  │
│  - role_bindings                  │     │  - courses                         │
│  - audit_log                      │     │  - enrollments                     │
└─────────────────────────────────┘     │  - grades                          │
                                         │  - attendance                      │
                                         │  - faculty                         │
                                         │  - advisee_mapping                 │
                                         └──────────────────────────────────┘
```

The AURA Auth DB is tiny and AURA-owned — it holds the identity/mapping layer. The ERP DB is large and DAU-owned — AURA only ever reads from it via a locked-down service account. If the ERP team is unwilling to give direct DB access (common), the ERP Connector Service (file 05) can alternatively call the ERP's existing REST API instead.

---

## AURA Auth DB tables

```sql
-- ─────────────────────────────────────────────────────────────────
-- users: one row per person who has ever logged into AURA
-- source of truth for AURA-side identity mapping
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,       -- parth.a@daiict.ac.in
    erp_id        TEXT UNIQUE NOT NULL,       -- roll number or employee ID
                                               -- from ERP, used to join
    role          TEXT NOT NULL               -- 'student'|'faculty'|'admin'
                  CHECK (role IN ('student', 'faculty', 'admin')),
    dept          TEXT,                       -- 'ICT', 'HSS', etc.
    display_name  TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT now(),
    last_login    TIMESTAMPTZ
);

-- Index for fast lookup by email (happens on every login)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_erp_id ON users(erp_id);


-- ─────────────────────────────────────────────────────────────────
-- sessions: tracks active refresh tokens for revocation
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,  -- bcrypt-hashed, not plain
    issued_at     TIMESTAMPTZ DEFAULT now(),
    expires_at    TIMESTAMPTZ NOT NULL,
    revoked       BOOLEAN NOT NULL DEFAULT FALSE,
    user_agent    TEXT,   -- for display in "active sessions" UI
    ip_address    INET    -- logged at issue time only, not per-request
);

CREATE INDEX idx_sessions_user ON sessions(user_id);


-- ─────────────────────────────────────────────────────────────────
-- role_bindings: fine-grained extra permissions beyond base role
-- e.g. a faculty member marked as Dean of Students gets access to
-- aggregate student data across all departments
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE role_bindings (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    binding       TEXT NOT NULL,
    -- Examples of valid bindings:
    -- 'class_advisor:{dept}:{batch}'
    --     e.g. 'class_advisor:ICT:2024'
    --     grants read on all students in that dept+batch
    -- 'course_instructor:{course_code}'
    --     e.g. 'course_instructor:IT205'
    --     grants read on enrolled students' attendance/grades for IT205
    -- 'dean_of_students'
    --     grants aggregate (not individual) student data access
    -- 'exam_committee'
    --     grants read on all grades for the current semester
    -- 'admin_full'
    --     grants unrestricted read (only for registrar/IT admin)
    granted_by    UUID REFERENCES users(id),
    granted_at    TIMESTAMPTZ DEFAULT now(),
    expires_at    TIMESTAMPTZ,     -- NULL = permanent until revoked
    revoked       BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_role_bindings_user ON role_bindings(user_id);


-- ─────────────────────────────────────────────────────────────────
-- audit_log: immutable record of every personal-data query
-- NEVER delete or update rows in this table
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ DEFAULT now() NOT NULL,
    user_id         UUID NOT NULL,   -- who asked
    erp_id          TEXT NOT NULL,   -- their ERP ID at query time
    role            TEXT NOT NULL,   -- their role at query time
    query_text      TEXT NOT NULL,   -- the original user query
    query_type      TEXT NOT NULL,   -- 'public'|'personal'|'mixed'
    target_erp_id   TEXT,            -- whose data was accessed
                                      -- NULL if own data or public
    access_granted  BOOLEAN NOT NULL,
    denial_reason   TEXT,            -- populated if access_granted=FALSE
    erp_tables      TEXT[]           -- which ERP tables were queried
);

-- Append-only enforcement: grant INSERT but not UPDATE/DELETE
-- to the AURA app's DB user:
-- GRANT INSERT ON audit_log TO aura_app;
-- REVOKE UPDATE, DELETE ON audit_log FROM aura_app;
```

---

## ERP DB — tables AURA needs READ access to

AURA does not own these tables. The ERP team grants a read-only service account (`aura_readonly`) access to specific columns only — not `SELECT *` on the full table.

```sql
-- Grant examples for ERP team to run on their database:

-- Students
GRANT SELECT (
    roll_number, full_name, dept, batch_year, program,
    current_semester, enrollment_status
) ON students TO aura_readonly;

-- Academic record (CGPA, SPI per semester)
GRANT SELECT (
    roll_number, semester, spi, cpi
) ON academic_record TO aura_readonly;

-- Course grades
GRANT SELECT (
    roll_number, course_code, course_name,
    semester, grade, grade_points
) ON course_grades TO aura_readonly;

-- Attendance
GRANT SELECT (
    roll_number, course_code, semester,
    total_classes, attended_classes, attendance_pct
) ON attendance TO aura_readonly;

-- Faculty
GRANT SELECT (
    employee_id, full_name, dept, designation, email
) ON faculty TO aura_readonly;

-- Who is teaching which course
GRANT SELECT (
    employee_id, course_code, semester, batch
) ON course_assignments TO aura_readonly;

-- Faculty advisor → student mapping
GRANT SELECT (
    advisor_employee_id, student_roll_number, start_date, end_date
) ON advisee_mapping TO aura_readonly;

-- Enrolled students per course (for faculty checking their course)
GRANT SELECT (
    roll_number, course_code, semester
) ON enrollments TO aura_readonly;

-- NOTE: deliberately NOT granting access to:
-- - passwords, OTP secrets, payment info
-- - disciplinary records (separate system)
-- - medical records
-- - parent/guardian contact info
-- - hostel room allocation with exact room numbers
--   (floor/wing is ok for general queries; exact room is private)
```

---

## The mapping between these two databases

The join key is `users.erp_id` (AURA Auth DB) ↔ `students.roll_number` or `faculty.employee_id` (ERP DB). This one field is what lets AURA say "the logged-in user with email parth.a@daiict.ac.in has roll_number 202301234, so fetch academic_record WHERE roll_number = '202301234'".

This join happens inside the ERP Connector Service (file 05), never in AURA's main chat code. The main chat code only ever passes the `identity` object — it never directly constructs any SQL.
