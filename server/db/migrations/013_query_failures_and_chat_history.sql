-- ============================================================
-- 013_query_failures_and_chat_history.sql
--
-- Adds:
-- 1. query_failures — captures failed, rejected, or degraded queries across
--    guardrails, access control, retrieval, tool execution, LLM timeout, and generation.
--    Carries langsmith_run_id for direct 1-click trace debugging.
-- 2. chat_threads & chat_messages — centralized database store for user chat
--    conversations and multi-turn debug tracking.
-- ============================================================

-- ── 1. Query Failures ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS query_failures (
    id              SERIAL PRIMARY KEY,
    query_text      TEXT NOT NULL,
    failure_stage   VARCHAR(64) NOT NULL,    -- 'guardrail', 'access_control', 'retrieval', 'tool_execution', 'llm_generation', 'context_budget', 'database'
    failure_code    VARCHAR(64) NOT NULL,    -- 'RETRIEVAL_EMPTY', 'GUARDRAIL_BLOCKED', 'VLLM_TIMEOUT', 'AURA-CTX-001', 'AURA-GEN-002', etc.
    error_message   TEXT,
    user_role       VARCHAR(32),             -- 'student', 'faculty', 'guest', 'admin'
    erp_id          VARCHAR(64),
    thread_id       VARCHAR(64),
    langsmith_run_id VARCHAR(128),
    latency_ms      INTEGER,
    metadata        JSONB DEFAULT '{}'::jsonb,
    resolved_at     TIMESTAMPTZ,
    resolved_by     VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_failures_created_at ON query_failures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_failures_stage ON query_failures(failure_stage);
CREATE INDEX IF NOT EXISTS idx_query_failures_code ON query_failures(failure_code);
CREATE INDEX IF NOT EXISTS idx_query_failures_thread ON query_failures(thread_id);

-- ── 2. Chat Threads & Messages ──────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_threads (
    id              VARCHAR(64) PRIMARY KEY,
    erp_id          VARCHAR(64),
    role            VARCHAR(32) NOT NULL DEFAULT 'student',
    title           VARCHAR(500) NOT NULL DEFAULT 'New Chat',
    last_activity   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_threads_erp_id ON chat_threads(erp_id);
CREATE INDEX IF NOT EXISTS idx_chat_threads_last_activity ON chat_threads(last_activity DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    id              SERIAL PRIMARY KEY,
    thread_id       VARCHAR(64) NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
    role            VARCHAR(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    is_personal_data BOOLEAN NOT NULL DEFAULT FALSE,
    sources         JSONB DEFAULT '[]'::jsonb,
    langsmith_run_id VARCHAR(128),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_created ON chat_messages(thread_id, created_at ASC);

-- Conditional role grants for production aura_app user
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aura_app') THEN
        GRANT SELECT, INSERT ON query_failures TO aura_app;
        GRANT USAGE, SELECT ON SEQUENCE query_failures_id_seq TO aura_app;

        GRANT SELECT, INSERT, UPDATE, DELETE ON chat_threads TO aura_app;
        GRANT SELECT, INSERT ON chat_messages TO aura_app;
        GRANT USAGE, SELECT ON SEQUENCE chat_messages_id_seq TO aura_app;
    END IF;
END $$;
