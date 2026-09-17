-- ============================================================
-- 012_bug_reports_admin.sql
--
-- Extends bug_reports (009_bug_reports.sql) to support the admin bug
-- resolver dashboard:
--   * category      — student/faculty picks this in the report form so
--                     the stats tab can break volume down by area.
--   * status        — open -> in_progress -> resolved workflow.
--   * updated_at    — bumped whenever status changes.
--   * resolved_at / resolved_by — who closed it and when, for auditing.
--
-- 009_bug_reports.sql intentionally revoked UPDATE on bug_reports from
-- aura_app (reports were write-once from the reporter's side). The admin
-- dashboard now needs to move a report through the workflow, so this
-- migration re-grants UPDATE, but ONLY on the columns the dashboard is
-- allowed to touch (status/updated_at/resolved_at/resolved_by) — the
-- original report fields (query_text, image_path, erp_id, role) stay
-- immutable at the DB-grant level, not just by convention.
-- ============================================================

ALTER TABLE bug_reports
    ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'other'
        CHECK (category IN (
            'chat_ai',        -- wrong/broken AURA chat answers
            'timetable',
            'calendar',
            'login_auth',
            'performance',
            'ui_ux',
            'other'
        ));

ALTER TABLE bug_reports
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'resolved'));

ALTER TABLE bug_reports
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE bug_reports
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

-- Nullable, no FK: mirrors erp_id's own note in 009 — we want a durable
-- record of who resolved it even if the admin's identity record changes.
ALTER TABLE bug_reports
    ADD COLUMN IF NOT EXISTS resolved_by TEXT;

CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status);
CREATE INDEX IF NOT EXISTS idx_bug_reports_category ON bug_reports(category);

-- Column-level grant: aura_app may update only the workflow columns, never
-- the original submission fields, and still cannot DELETE.
GRANT UPDATE (status, updated_at, resolved_at, resolved_by) ON bug_reports TO aura_app;
