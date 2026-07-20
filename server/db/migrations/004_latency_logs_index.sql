-- Migration: Add index to latency_logs.created_at
CREATE INDEX IF NOT EXISTS idx_latency_logs_created_at ON latency_logs(created_at);
