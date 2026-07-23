-- ============================================================
-- 004_student_profile_and_timetable.sql
--
-- Adds to the AURA Auth DB (NOT the ERP DB — this data is entirely
-- AURA-owned, unlike academic_record/grades/fees/attendance which
-- remain ERP-only and read-only per the architecture doc):
--
--   1. Student profile fields on user_identity_map — full_name,
--      current_year, current_sem, current_sec. Populated once at
--      Google SSO login time (see resolve-identity) so AURA can
--      resolve "which timetable belongs to this student" without
--      ever touching the ERP DB.
--
--   2. timetable_master — the canonical class schedule for a given
--      (year, sem, sec) cohort. Seeded from the demo timetable via
--      server/scripts/import_timetable.py. Admin-managed only.
--
--   3. timetable_overrides — per-student, additive/replacing edits
--      on top of timetable_master. This is the one deliberately
--      writable, per-user table in the whole platform: a student
--      can ask AURA in chat to change something in their own
--      timetable, and only their own view changes. It never touches
--      timetable_master or any other student's row.
--
--   4. push_subscriptions — Web Push endpoints for the "10 minutes
--      before class" browser/PWA notification.
-- ============================================================

-- ── Student profile fields ──────────────────────────────────────
ALTER TABLE user_identity_map
    ADD COLUMN IF NOT EXISTS full_name     TEXT,
    ADD COLUMN IF NOT EXISTS current_year  SMALLINT,   -- 1..5
    ADD COLUMN IF NOT EXISTS current_sem   SMALLINT,   -- 1..10
    ADD COLUMN IF NOT EXISTS current_sec   TEXT;        -- 'A', 'B', 'C1' etc.

CREATE INDEX IF NOT EXISTS idx_identity_cohort
    ON user_identity_map(current_year, current_sem, current_sec);

-- ── timetable_master ────────────────────────────────────────────
-- One row per recurring weekly class slot for a cohort.
-- day_of_week: 0=Monday .. 6=Sunday (ISO-ish, no classes on 6 normally).
CREATE TABLE IF NOT EXISTS timetable_master (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year          SMALLINT NOT NULL,
    sem           SMALLINT NOT NULL,
    sec           TEXT NOT NULL,
    day_of_week   SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time    TIME NOT NULL,
    end_time      TIME NOT NULL,
    course_code   TEXT NOT NULL,
    course_name   TEXT NOT NULL,
    session_type  TEXT NOT NULL DEFAULT 'lecture'
                  CHECK (session_type IN ('lecture', 'lab', 'tutorial')),
    room          TEXT,
    faculty_name  TEXT,
    credits       TEXT,
    course_type   TEXT,
    batch_raw     TEXT,
    branch        TEXT,
    program       TEXT,
    semester_label TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_timetable_master_cohort
    ON timetable_master(year, sem, sec, day_of_week);

CREATE INDEX IF NOT EXISTS idx_timetable_master_faculty
    ON timetable_master(faculty_name);

-- ── timetable_overrides ─────────────────────────────────────────
-- Per-student customisations layered on top of timetable_master at
-- read time. Never mutates timetable_master or any other student's
-- data — every row is scoped by erp_id and every write path requires
-- the requester's own verified identity (see pipeline/timetable).
--
-- kind:
--   'replace' — overrides a specific master slot (matched by
--               master_id) with new time/room/etc for this student only
--   'add'     — a brand-new slot that only exists for this student
--   'remove'  — hides a specific master slot for this student only
CREATE TABLE IF NOT EXISTS timetable_overrides (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erp_id        TEXT NOT NULL,
    kind          TEXT NOT NULL CHECK (kind IN ('replace', 'add', 'remove')),
    master_id     UUID REFERENCES timetable_master(id) ON DELETE CASCADE,
    day_of_week   SMALLINT CHECK (day_of_week BETWEEN 0 AND 6),
    start_time    TIME,
    end_time      TIME,
    course_code   TEXT,
    course_name   TEXT,
    session_type  TEXT CHECK (session_type IN ('lecture', 'lab', 'tutorial')),
    room          TEXT,
    faculty_name  TEXT,
    credits       TEXT,
    course_type   TEXT,
    batch_raw     TEXT,
    branch        TEXT,
    program       TEXT,
    semester_label TEXT,
    note          TEXT,             -- what the student asked for, for audit/undo
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_timetable_overrides_erp
    ON timetable_overrides(erp_id) WHERE is_active;

-- ── push_subscriptions ──────────────────────────────────────────
-- One row per browser/device the student has enabled notifications on.
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erp_id        TEXT NOT NULL,
    endpoint      TEXT UNIQUE NOT NULL,
    p256dh        TEXT NOT NULL,
    auth_key      TEXT NOT NULL,
    user_agent    TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT now(),
    last_seen_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_erp ON push_subscriptions(erp_id) WHERE is_active;

-- ── notification_log ────────────────────────────────────────────
-- Dedup guard so a class doesn't fire its "10 min before" reminder
-- twice (e.g. if the scheduler tick overlaps or the process restarts).
-- Falls back to this table when Redis is unavailable — see
-- pipeline/redis_client.py for the primary (fast) dedup path.
CREATE TABLE IF NOT EXISTS notification_log (
    id            BIGSERIAL PRIMARY KEY,
    erp_id        TEXT NOT NULL,
    class_date    DATE NOT NULL,
    start_time    TIME NOT NULL,
    course_code   TEXT NOT NULL,
    sent_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE (erp_id, class_date, start_time, course_code)
);

-- ── Grants ────────────────────────────────────────────────────
GRANT SELECT, INSERT, UPDATE ON timetable_master     TO aura_app;
GRANT SELECT, INSERT, UPDATE ON timetable_overrides  TO aura_app;
GRANT SELECT, INSERT, UPDATE ON push_subscriptions   TO aura_app;
GRANT SELECT, INSERT         ON notification_log     TO aura_app;
