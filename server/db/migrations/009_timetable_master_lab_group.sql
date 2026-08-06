-- ============================================================
-- 009_timetable_master_lab_group.sql
--
-- Adds support for Lab Timetables and Lab Group selections.
-- ============================================================

ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS lab_group VARCHAR(10);
ALTER TABLE user_identity_map ADD COLUMN IF NOT EXISTS current_lab_group VARCHAR(10);
