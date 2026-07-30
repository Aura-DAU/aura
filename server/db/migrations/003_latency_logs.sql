-- Migration: Create latency_logs table
CREATE TABLE IF NOT EXISTS latency_logs (
    id SERIAL PRIMARY KEY,
    guardrail_time DOUBLE PRECISION NOT NULL,
    retrieval_time DOUBLE PRECISION NOT NULL,
    generation_time DOUBLE PRECISION NOT NULL,
    total_time DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
