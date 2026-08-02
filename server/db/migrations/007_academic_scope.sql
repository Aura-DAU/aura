-- Canonical, server-side academic context for student-aware retrieval.
-- Identity remains in user_identity_map; these tables separate stable derived
-- identity, slowly changing academic profile, and frequent enrolment changes.

CREATE TABLE IF NOT EXISTS student_identity (
    erp_id                  TEXT PRIMARY KEY REFERENCES user_identity_map(erp_id),
    admission_year          SMALLINT NOT NULL CHECK (admission_year BETWEEN 2000 AND 2100),
    programme_id            TEXT NOT NULL,
    branch_id               TEXT,
    department_id           TEXT,
    degree_level            TEXT NOT NULL CHECK (degree_level IN ('undergraduate', 'postgraduate', 'doctoral')),
    derivation_rule_version TEXT NOT NULL,
    identity_version        INTEGER NOT NULL DEFAULT 1 CHECK (identity_version > 0),
    resolved_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_student_identity_programme_batch
    ON student_identity(programme_id, admission_year);

CREATE TABLE IF NOT EXISTS student_academic_profile (
    erp_id                   TEXT PRIMARY KEY REFERENCES student_identity(erp_id),
    academic_status          TEXT NOT NULL CHECK (academic_status IN ('active', 'leave', 'graduated', 'suspended', 'unknown')),
    expected_graduation_year SMALLINT CHECK (expected_graduation_year BETWEEN 2000 AND 2100),
    curriculum_version       TEXT,
    regulation_version       TEXT,
    source_system            TEXT NOT NULL,
    source_record_version    TEXT,
    profile_version          INTEGER NOT NULL DEFAULT 1 CHECK (profile_version > 0),
    synced_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_academic_profile_active
    ON student_academic_profile(academic_status) WHERE academic_status = 'active';

CREATE TABLE IF NOT EXISTS student_academic_profile_history (
    erp_id                TEXT NOT NULL REFERENCES student_identity(erp_id),
    profile_version       INTEGER NOT NULL CHECK (profile_version > 0),
    academic_status       TEXT NOT NULL,
    expected_graduation_year SMALLINT,
    curriculum_version    TEXT,
    regulation_version    TEXT,
    source_system         TEXT NOT NULL,
    source_record_version TEXT,
    changed_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    change_reason         TEXT NOT NULL,
    PRIMARY KEY (erp_id, profile_version)
);

CREATE TABLE IF NOT EXISTS student_enrollment_snapshot (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erp_id                TEXT NOT NULL REFERENCES student_identity(erp_id),
    academic_term         TEXT NOT NULL,
    current_semester      SMALLINT CHECK (current_semester BETWEEN 1 AND 20),
    minor_id              TEXT,
    honours_status        TEXT,
    source_system         TEXT NOT NULL,
    source_record_version TEXT,
    captured_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_current            BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_enrollment_snapshot_current
    ON student_enrollment_snapshot(erp_id) WHERE is_current;

CREATE TABLE IF NOT EXISTS student_course_enrollment (
    snapshot_id     UUID NOT NULL REFERENCES student_enrollment_snapshot(id) ON DELETE CASCADE,
    course_code     TEXT NOT NULL,
    enrollment_type TEXT NOT NULL CHECK (enrollment_type IN ('core', 'elective', 'minor', 'honours', 'other')),
    PRIMARY KEY (snapshot_id, course_code)
);

GRANT SELECT, INSERT, UPDATE ON student_identity TO aura_app;
GRANT SELECT, INSERT, UPDATE ON student_academic_profile TO aura_app;
GRANT SELECT, INSERT ON student_academic_profile_history TO aura_app;
GRANT SELECT, INSERT, UPDATE ON student_enrollment_snapshot TO aura_app;
GRANT SELECT, INSERT, UPDATE ON student_course_enrollment TO aura_app;
