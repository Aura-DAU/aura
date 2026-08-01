-- Migration 009: exam_schedule
-- Stores upcoming exam dates, times, venues per course/cohort.
-- Populated manually or via xlsx_parser import workflow.
-- get_upcoming_exams() in service.py queries this table.

CREATE TABLE IF NOT EXISTS exam_schedule (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    course_code  TEXT        NOT NULL,
    course_name  TEXT,
    exam_date    DATE        NOT NULL,
    start_time   TIME        NOT NULL,
    end_time     TIME        NOT NULL,
    venue        TEXT,
    year         INT,                      -- NULL means applies to all years
    sem          INT,                      -- NULL means applies to all semesters
    branch       TEXT,                     -- NULL means all branches
    program      TEXT,                     -- e.g. 'BTech', 'MTech'
    created_at   TIMESTAMPTZ DEFAULT now(),
    updated_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exam_schedule_date
    ON exam_schedule(exam_date);

CREATE INDEX IF NOT EXISTS idx_exam_schedule_course
    ON exam_schedule(course_code);

CREATE INDEX IF NOT EXISTS idx_exam_schedule_cohort
    ON exam_schedule(year, sem);

COMMENT ON TABLE exam_schedule IS
    'Upcoming exam schedule entries. Imported from official exam timetable spreadsheets.';
