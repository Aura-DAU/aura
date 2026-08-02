-- ============================================================
-- 007_timetable_master_course_columns.sql
--
-- Adds the course-classification and faculty-view columns that the
-- timetable read path (rag/pipeline/timetable/service.py) SELECTs but
-- that 004_student_profile_and_timetable.sql never created. Their
-- absence made get_master_rows / get_elective_rows / get_faculty_rows
-- fail with `UndefinedColumn`, surfacing as a 502 on /timetable:
--   - course_type : core vs elective classification (see _is_elective)
--   - program     : programme label; also matched in the elective filter
--   - batch_raw   : raw batch string shown in the faculty timetable
--   - branch      : branch label shown in the faculty timetable
--   - credits     : course credits shown in the faculty timetable
--
-- Nullable and backfill-free: import_timetable.py does not populate these
-- yet, so existing rows stay NULL. The read path already treats a missing
-- value as "unset" (row.get(col, "") / _is_elective(None) -> False), so
-- NULL columns unblock the queries without changing displayed timetables.
-- Table-level grants from 004 cover the new columns automatically.
-- ============================================================

ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS course_type TEXT;
ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS program     TEXT;
ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS batch_raw   TEXT;
ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS branch      TEXT;
ALTER TABLE timetable_master ADD COLUMN IF NOT EXISTS credits     TEXT;
