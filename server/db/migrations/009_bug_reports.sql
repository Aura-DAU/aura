-- ============================================================
-- 009_bug_reports.sql — Bug Report submissions
--
-- Stores bug reports submitted by students and faculty via the
-- "Report a Bug" panel in the AURA chat interface.
-- Image attachments are stored on disk; only the relative path
-- is recorded here (NULL when no image was uploaded).
-- ============================================================

CREATE TABLE IF NOT EXISTS bug_reports (
    id          BIGSERIAL PRIMARY KEY,
    erp_id      TEXT        NOT NULL,
    role        TEXT        NOT NULL,
    query_text  TEXT        NOT NULL,
    image_path  TEXT,                       -- NULL when no screenshot attached
    created_at  TIMESTAMPTZ DEFAULT now()   NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bug_reports_erp_id     ON bug_reports(erp_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_created_at ON bug_reports(created_at DESC);

-- aura_app may INSERT and SELECT; no UPDATE/DELETE (keep the audit trail intact).
GRANT INSERT, SELECT ON bug_reports             TO aura_app;
GRANT USAGE, SELECT  ON SEQUENCE bug_reports_id_seq TO aura_app;
