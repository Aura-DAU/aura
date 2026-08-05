-- Student/faculty "Report a Bug" submissions from the sidebar panel.
-- erp_id/role are captured at submission time (not FK'd live off the JWT)
-- so a report still records who filed it even if their identity record
-- changes later. image_path is a relative path under BUG_REPORT_UPLOAD_DIR,
-- never a client-controlled absolute path — see bug_report_routes.py.

CREATE TABLE IF NOT EXISTS bug_reports (
    id          SERIAL PRIMARY KEY,
    erp_id      TEXT NOT NULL REFERENCES user_identity_map(erp_id),
    role        TEXT NOT NULL,
    query_text  TEXT NOT NULL CHECK (char_length(query_text) BETWEEN 1 AND 5000),
    image_path  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bug_reports_erp_id ON bug_reports(erp_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_created_at ON bug_reports(created_at);

-- aura_app may file and list reports but never edit/delete existing ones.
GRANT SELECT, INSERT ON bug_reports TO aura_app;
REVOKE UPDATE, DELETE ON bug_reports FROM aura_app;
GRANT USAGE, SELECT ON SEQUENCE bug_reports_id_seq TO aura_app;