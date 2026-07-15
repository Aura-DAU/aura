-- ============================================================
-- 001_auth_schema.sql — AURA Auth Database (SSO architecture)
--
-- Authentication is handled entirely by NextAuth.js (Google SSO).
-- FastAPI never issues tokens, never stores passwords, never manages
-- sessions. It only:
--   1. Answers GET /internal/resolve-identity?email=... (called once
--      per user login by Next.js during the NextAuth jwt callback)
--   2. Verifies the short-lived internal JWT that Next.js mints and
--      attaches to every request header.
--
-- Therefore this schema has NO users table, NO sessions table,
-- NO password columns. Three tables only:
--   user_identity_map  — email → erp_id + role mapping (no auth data)
--   role_bindings      — fine-grained extra permissions for faculty
--   audit_log          — append-only record of every personal-data query
-- ============================================================

-- ── user_identity_map ─────────────────────────────────────────
-- Maps an institutional Google email to the ERP identity that AURA
-- needs for data access. No passwords, no tokens, no sessions.
-- Populated by seed_identity_map.py and re-synced each semester.
CREATE TABLE IF NOT EXISTS user_identity_map (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,   -- parth.a@daiict.ac.in
    erp_id      TEXT UNIQUE NOT NULL,   -- roll number or employee ID
    role        TEXT NOT NULL
                CHECK (role IN ('student', 'faculty', 'admin')),
    dept        TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_identity_email  ON user_identity_map(email);
CREATE INDEX IF NOT EXISTS idx_identity_erp_id ON user_identity_map(erp_id);

-- ── role_bindings ─────────────────────────────────────────────
-- Fine-grained extra permissions beyond base role, keyed on erp_id.
-- Valid binding strings:
--   'class_advisor:{dept}:{batch}'   e.g. 'class_advisor:ICT:2024'
--   'course_instructor:{code}'       e.g. 'course_instructor:IT205'
--   'dean_of_students'
--   'exam_committee'
--   'admin_full'
CREATE TABLE IF NOT EXISTS role_bindings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erp_id      TEXT NOT NULL,           -- FK to user_identity_map.erp_id
    binding     TEXT NOT NULL,
    granted_by  TEXT,                    -- erp_id of admin who granted this
    granted_at  TIMESTAMPTZ DEFAULT now(),
    expires_at  TIMESTAMPTZ,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_role_bindings_erp ON role_bindings(erp_id);

-- ── audit_log ─────────────────────────────────────────────────
-- Append-only. Never UPDATE or DELETE rows from this table.
-- The aura_app role gets INSERT only (no UPDATE/DELETE) — enforced below.
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ DEFAULT now() NOT NULL,
    erp_id          TEXT NOT NULL,       -- who asked
    role            TEXT NOT NULL,       -- their role at query time
    query_text      TEXT NOT NULL,
    query_type      TEXT NOT NULL,       -- 'public'|'personal'|'mixed'|'aggregate'
    target_erp_id   TEXT,               -- whose data was accessed (NULL = own/public)
    access_granted  BOOLEAN NOT NULL,
    denial_reason   TEXT,
    erp_tables      TEXT[]
);

-- ── Grants ────────────────────────────────────────────────────
GRANT SELECT, INSERT, UPDATE ON user_identity_map TO aura_app;
GRANT SELECT, INSERT, UPDATE ON role_bindings     TO aura_app;
-- audit_log is APPEND-ONLY:
GRANT INSERT, SELECT         ON audit_log         TO aura_app;
REVOKE UPDATE, DELETE        ON audit_log         FROM aura_app;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq  TO aura_app;
