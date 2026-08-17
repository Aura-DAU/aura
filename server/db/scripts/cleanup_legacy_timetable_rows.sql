-- cleanup_legacy_timetable_rows.sql
--
-- One-time cleanup for the timetable_master row pollution diagnosed via:
--   SELECT semester_label, year, sem, sec, course_code, day_of_week,
--          start_time, count(*)
--   FROM timetable_master WHERE course_code = 'IT314'
--   GROUP BY semester_label, year, sem, sec, course_code, day_of_week, start_time
--   ORDER BY semester_label, sec, day_of_week;
--
-- Two known sources of junk, both because reads never filtered on
-- semester_label until CURRENT_SEMESTER_LABEL was added to service.py:
--
--   1. server/scripts/load_timetable.sql -- a demo/dev seed script that was
--      run directly against production at some point. It never sets
--      semester_label (NULL on every row it inserts) and used placeholder
--      strings ('MTech', 'BS-IT', 'BS-DS-AI') in the `sec` column instead
--      of real section letters.
--   2. Any earlier real import (import_timetable_xlsx.py --semester "X")
--      run with a different --semester string than the current one --
--      those rows are real data, just for a semester that is no longer
--      current, and get_master_rows never excluded them before.
--
-- SAFE ORDER OF OPERATIONS:
--   1. Run the SELECT below first and read the output. Confirm which rows
--      you expect to keep (semester_label = the CURRENT_SEMESTER_LABEL
--      you're about to set in .env) before deleting anything.
--   2. Take a Postgres backup / pg_dump of timetable_master first --
--      these DELETEs are not reversible.
--   3. Then run the DELETE with the real current semester label substituted.

-- ── Step 1: inspect what's actually in there ─────────────────────
SELECT semester_label, year, sem, sec, count(*) AS n
FROM timetable_master
GROUP BY semester_label, year, sem, sec
ORDER BY semester_label NULLS FIRST, year, sem, sec;

-- ── Step 2: back this up before deleting (run from the shell, not psql) ──
--   pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t timetable_master \
--     > timetable_master_backup_$(date +%Y%m%d).sql

-- ── Step 3: delete legacy demo-seed junk (load_timetable.sql rows) ───
-- These never had a real semester_label and use placeholder sec values.
DELETE FROM timetable_master
WHERE semester_label IS NULL
  AND sec IN ('MTech', 'BS-IT', 'BS-DS-AI');

-- ── Step 4: delete everything that isn't the current semester ────────
-- Uncomment and fill in the real label (must match exactly what you set
-- as CURRENT_SEMESTER_LABEL in deploy/node1/.env, e.g. 'Autumn 2026-27').
-- Review Step 1's output first -- if there are other semesters you
-- genuinely want to keep queryable, don't run this blanket delete;
-- narrow the WHERE clause instead.
--
-- DELETE FROM timetable_master
-- WHERE semester_label IS DISTINCT FROM 'Autumn 2026-27';

-- ── Step 5: verify ─────────────────────────────────────────────────
-- SELECT semester_label, year, sem, sec, count(*) FROM timetable_master
-- GROUP BY semester_label, year, sem, sec ORDER BY 1,2,3,4;
