-- ============================================================
-- 006_student_elective_selections.sql
--
-- Stores which elective courses each student has opted for.
-- Core courses (course_type NOT ILIKE '%elective%') are always
-- shown to every student in the cohort. Elective courses are
-- only shown if the student has a row in this table for that
-- master slot.
--
-- Backward-compatible: if a student has ZERO rows here, the
-- timetable view shows ALL courses (core + all electives).
-- Filtering only kicks in once the student saves at least one
-- selection.
-- ============================================================

CREATE TABLE IF NOT EXISTS student_elective_selections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erp_id      TEXT NOT NULL,
    master_id   UUID NOT NULL REFERENCES timetable_master(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- One student can only select the same master slot once
CREATE UNIQUE INDEX IF NOT EXISTS idx_elective_sel_unique
    ON student_elective_selections(erp_id, master_id);

-- Fast lookup: "what electives has this student selected?"
CREATE INDEX IF NOT EXISTS idx_elective_sel_erp
    ON student_elective_selections(erp_id);

-- Grants
GRANT SELECT, INSERT, DELETE ON student_elective_selections TO aura_app;
