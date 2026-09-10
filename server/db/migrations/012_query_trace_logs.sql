-- ============================================================
-- 012_query_trace_logs.sql — AURA V2 Query Traceability & Failure Telemetry
--
-- Records a structured trace for every query processed by the AURA chat
-- pipeline (both streaming and non-streaming): query text, user identity,
-- execution status, failure stage/reason, retrieved sources, returned answer,
-- and per-stage latency breakdown.
-- ============================================================

CREATE TABLE IF NOT EXISTS query_trace_logs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at              TIMESTAMPTZ DEFAULT now() NOT NULL,

    erp_id                  TEXT,
    user_role               TEXT NOT NULL,
    user_dept               TEXT,

    query_text              TEXT NOT NULL,
    query_type              TEXT,

    status                  TEXT NOT NULL,

    failure_stage           TEXT,
    failure_reason          TEXT,

    sources_fetched         JSONB DEFAULT '[]'::jsonb,
    sources_count           INT DEFAULT 0,

    answer_preview          TEXT,

    latency_total_ms        INT,
    latency_guardrail_ms    INT,
    latency_retrieval_ms    INT,
    latency_generation_ms   INT,

    is_personal_data        BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_query_trace_created_at
ON query_trace_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_trace_status
ON query_trace_logs(status);

CREATE INDEX IF NOT EXISTS idx_query_trace_failure_stage
ON query_trace_logs(failure_stage);

CREATE INDEX IF NOT EXISTS idx_query_trace_erp_id
ON query_trace_logs(erp_id);

CREATE INDEX IF NOT EXISTS idx_query_trace_user_role
ON query_trace_logs(user_role);

CREATE INDEX IF NOT EXISTS idx_query_trace_status_created
ON query_trace_logs(status, created_at DESC);

-- Grant privileges to application role if it exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'aura_app') THEN
        GRANT SELECT, INSERT ON query_trace_logs TO aura_app;
    END IF;
END
$$;
