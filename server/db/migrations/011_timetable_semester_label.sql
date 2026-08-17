-- ============================================================
-- 011_timetable_semester_label.sql
--
-- Adds timetable_master.semester_label, which import_timetable_xlsx.py
-- has required (both for its cleanup DELETE and its INSERT) since it
-- replaced the CSV importer -- but which no prior migration ever created.
-- It has been living on production as an out-of-band, hand-run ALTER TABLE
-- that this migration file never captured, meaning a fresh Postgres volume
-- (new node1, disaster recovery, a second environment) would apply
-- 001-010 cleanly and then immediately fail on the first
-- `import_timetable_xlsx.py --semester "..."` with:
--   psycopg2.errors.UndefinedColumn: column "semester_label" of relation
--   "timetable_master" does not exist
--
-- This migration is idempotent (IF NOT EXISTS) so it is safe to apply even
-- though the column may already exist on the current production DB from
-- the earlier manual ALTER -- it exists purely to make the schema
-- reproducible from migrations alone, which it was not before.
--
-- Root-cause note (see also service.py CURRENT_SEMESTER_LABEL): every
-- read path in rag/pipeline/timetable/service.py filtered on
-- (year, sem, sec) only, never on semester_label -- so rows from every
-- semester ever imported (plus legacy demo rows from
-- server/scripts/load_timetable.sql, which never set semester_label and
-- so are NULL here) were all being merged into one view. That is the
-- root cause of Section A/B timetable mixing. This migration only adds
-- the column; the actual filtering fix is CURRENT_SEMESTER_LABEL in
-- service.py, and stale rows still need the manual cleanup in
-- server/db/scripts/ (see cleanup_legacy_timetable_rows.sql) run once.
-- ============================================================

ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS semester_label TEXT;

-- Every real cohort-scoped read filters by (year, sem, sec, semester_label)
-- together once CURRENT_SEMESTER_LABEL is set -- index accordingly.
CREATE INDEX IF NOT EXISTS idx_timetable_master_semester
    ON timetable_master(semester_label, year, sem, sec);
