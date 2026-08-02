-- ============================================================
-- 002_extend_roles.sql — Extend audit_log for scope context
--
-- scope_context records fine-grained coordinator/dean scope for
-- richer audit trails (e.g. "coordinator:BTech-ICT").
-- ============================================================

ALTER TABLE audit_log
    ADD COLUMN IF NOT EXISTS scope_context TEXT;
