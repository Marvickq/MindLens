-- MindLens PostgreSQL Schema
-- PostgreSQL 15+
-- Core MVP schema for the FastAPI + SQLModel backend.
--
-- IMPORTANT:
--   1. The six dimension labels/item mappings must be replaced with the
--      exact research instrument definitions used by the project.
--   2. This schema stores deterministic outputs; it does NOT create
--      an individual clinical/self-harm risk score.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM (
    'COUNSELOR',
    'ADMIN'
);

CREATE TYPE case_status AS ENUM (
    'WAITING_FOR_RESPONSES',
    'READY_FOR_REVIEW',
    'UNDER_REVIEW',
    'COMPLETED',
    'ARCHIVED'
);

CREATE TYPE rater_type AS ENUM (
    'PARENT',
    'TEACHER',
    'ADOLESCENT'
);

CREATE TYPE session_status AS ENUM (
    'CREATED',
    'STARTED',
    'SUBMITTED',
    'EXPIRED',
    'REVOKED'
);

CREATE TYPE response_type AS ENUM (
    'LIKERT',
    'INTEGER',
    'BOOLEAN',
    'TEXT',
    'SINGLE_CHOICE'
);

CREATE TYPE signal_level AS ENUM (
    'NONE',
    'LOW',
    'MEANINGFUL'
);

CREATE TYPE counselor_action AS ENUM (
    'MONITOR',
    'REACH_OUT',
    'REFER'
);

CREATE TYPE actor_type AS ENUM (
    'COUNSELOR',
    'ADMIN',
    'RATER',
    'SYSTEM'
);

-- ============================================================
-- ORGANIZATION
-- ============================================================

CREATE TABLE organizations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- COUNSELOR / ADMIN
-- ============================================================

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL
                    REFERENCES organizations(id) ON DELETE RESTRICT,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(320) NOT NULL,
    password_hash   TEXT        NOT NULL,
    role            user_role   NOT NULL DEFAULT 'COUNSELOR',
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_org_email UNIQUE (organization_id, email)
);

CREATE INDEX idx_users_organization_id
    ON users(organization_id);

-- ============================================================
-- STUDENT CASE
-- ============================================================

CREATE TABLE student_cases (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID        NOT NULL
                        REFERENCES organizations(id) ON DELETE RESTRICT,
    external_reference  VARCHAR(255),
    display_name        VARCHAR(255) NOT NULL,
    grade               VARCHAR(50),
    school              VARCHAR(255),
    status              case_status NOT NULL DEFAULT 'WAITING_FOR_RESPONSES',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_student_cases_org_status
    ON student_cases(organization_id, status);

CREATE INDEX idx_student_cases_created_at
    ON student_cases(created_at DESC);

-- ============================================================
-- ASSESSMENT / QUESTIONNAIRE VERSION
-- ============================================================

CREATE TABLE assessment_versions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    version     VARCHAR(50) NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_assessment_version UNIQUE (name, version)
);

-- Seed default assessment version
INSERT INTO assessment_versions (name, version)
VALUES ('MindLens Clinical Dimensions v1', '1.0');

-- ============================================================
-- SIX DIMENSIONS
-- ============================================================

CREATE TABLE dimensions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_code  VARCHAR(100) NOT NULL UNIQUE,
    label           VARCHAR(255) NOT NULL,
    description     TEXT,
    display_order   INTEGER     NOT NULL,
    active          BOOLEAN     NOT NULL DEFAULT TRUE
);

-- Seed only as project placeholders.
-- Replace labels/mappings with the exact research instrument definitions.
INSERT INTO dimensions
    (dimension_code, label, description, display_order)
VALUES
    ('attention_persistence', 'Attention & Persistence',
     'Ability to maintain focus and persist through tasks across environments.', 1),
    ('activity',              'Activity',
     'Observable activity level and energy across settings.', 2),
    ('adaptability',          'Adaptability',
     'Ease of transitioning between activities and adapting to new situations.', 3),
    ('sensitivity',           'Sensitivity',
     'Responsiveness to sensory and emotional stimuli.', 4),
    ('sociability',           'Sociability',
     'Engagement and comfort in social interactions.', 5),
    ('self_regulation',       'Self-Regulation',
     'Capacity to manage emotions and impulses.', 6)
ON CONFLICT (dimension_code) DO NOTHING;

-- ============================================================
-- QUESTIONS
-- ============================================================

CREATE TABLE questions (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_version_id UUID          NOT NULL
                        REFERENCES assessment_versions(id) ON DELETE RESTRICT,
    dimension_id        UUID            NOT NULL
                        REFERENCES dimensions(id) ON DELETE RESTRICT,
    question_code       VARCHAR(100)    NOT NULL,
    question_text       TEXT            NOT NULL,
    response_type       response_type   NOT NULL,
    applicable_raters   rater_type[]    NOT NULL DEFAULT '{PARENT,TEACHER,ADOLESCENT}',
    required            BOOLEAN         NOT NULL DEFAULT TRUE,
    display_order       INTEGER         NOT NULL,
    validation_config   JSONB           NOT NULL DEFAULT '{}',
    active              BOOLEAN         NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_question_version_code
        UNIQUE (assessment_version_id, question_code)
);

CREATE INDEX idx_questions_version_dimension
    ON questions(assessment_version_id, dimension_id);

-- ============================================================
-- RATER INTAKE SESSION
-- ============================================================

CREATE TABLE rater_sessions (
    id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id     UUID            NOT NULL
                REFERENCES student_cases(id) ON DELETE CASCADE,
    rater_type  rater_type      NOT NULL,

    -- Store only a hash of the public intake token.
    token_hash  TEXT            NOT NULL UNIQUE,

    status      session_status  NOT NULL DEFAULT 'CREATED',
    expires_at  TIMESTAMPTZ     NOT NULL,
    started_at  TIMESTAMPTZ,
    submitted_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_case_rater_session
        UNIQUE (case_id, rater_type)
);

CREATE INDEX idx_rater_sessions_case
    ON rater_sessions(case_id);

CREATE INDEX idx_rater_sessions_token
    ON rater_sessions(token_hash);

-- ============================================================
-- RESPONSES
-- ============================================================

CREATE TABLE responses (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID    NOT NULL
                REFERENCES rater_sessions(id) ON DELETE CASCADE,
    question_id UUID    NOT NULL
                REFERENCES questions(id) ON DELETE RESTRICT,

    -- JSONB lets the backend support Likert/integer/boolean/text
    -- while Pydantic performs strict type/range validation.
    value       JSONB   NOT NULL,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_session_question
        UNIQUE (session_id, question_id)
);

CREATE INDEX idx_responses_session
    ON responses(session_id);

CREATE INDEX idx_responses_question
    ON responses(question_id);

-- ============================================================
-- DIMENSION SCORES
-- ============================================================

CREATE TABLE dimension_scores (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                 UUID            NOT NULL
                            REFERENCES student_cases(id) ON DELETE CASCADE,
    rater_type              rater_type      NOT NULL,
    dimension_id            UUID            NOT NULL
                            REFERENCES dimensions(id) ON DELETE RESTRICT,

    score                   NUMERIC(10, 4)  NOT NULL,

    questionnaire_version   VARCHAR(50)     NOT NULL,
    calculation_method      VARCHAR(100)    NOT NULL,
    calculation_version     VARCHAR(50)     NOT NULL,

    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_case_rater_dimension
        UNIQUE (case_id, rater_type, dimension_id)
);

CREATE INDEX idx_dimension_scores_case
    ON dimension_scores(case_id);

CREATE INDEX idx_dimension_scores_case_dimension
    ON dimension_scores(case_id, dimension_id);

-- ============================================================
-- DISCREPANCIES
-- ============================================================

CREATE TABLE discrepancies (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID            NOT NULL
                        REFERENCES student_cases(id) ON DELETE CASCADE,
    dimension_id        UUID            NOT NULL
                        REFERENCES dimensions(id) ON DELETE RESTRICT,

    rater_a             rater_type      NOT NULL,
    rater_b             rater_type      NOT NULL,

    score_a             NUMERIC(10, 4)  NOT NULL,
    score_b             NUMERIC(10, 4)  NOT NULL,

    divergence          NUMERIC(14, 6)  NOT NULL,
    signal_level        signal_level    NOT NULL DEFAULT 'NONE',

    calculation_method  VARCHAR(100)    NOT NULL,
    calculation_version VARCHAR(50)     NOT NULL,

    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_discrepancy_distinct_raters
        CHECK (rater_a <> rater_b),

    CONSTRAINT chk_discrepancy_rater_order
        CHECK (rater_a::TEXT < rater_b::TEXT),

    CONSTRAINT uq_case_dimension_rater_pair
        UNIQUE (case_id, dimension_id, rater_a, rater_b)
);

CREATE INDEX idx_discrepancies_case
    ON discrepancies(case_id);

CREATE INDEX idx_discrepancies_case_signal
    ON discrepancies(case_id, signal_level);

-- ============================================================
-- RESEARCH EVIDENCE
-- ============================================================

CREATE TABLE evidence (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_code       VARCHAR(100) NOT NULL UNIQUE,
    dimension_id        UUID
                        REFERENCES dimensions(id) ON DELETE RESTRICT,
    rater_pair          VARCHAR(50),
    title               VARCHAR(500) NOT NULL,
    source              TEXT        NOT NULL,
    source_type         VARCHAR(100),
    citation            TEXT,

    evidence_certainty  VARCHAR(100),
    study_count         INTEGER,
    sample_size         INTEGER,
    association_value   TEXT,
    limitation          TEXT,

    version             VARCHAR(50) NOT NULL DEFAULT '1.0',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_evidence_study_count
        CHECK (study_count IS NULL OR study_count >= 0),

    CONSTRAINT chk_evidence_sample_size
        CHECK (sample_size IS NULL OR sample_size >= 0)
);

-- Seed curated evidence records
INSERT INTO evidence (evidence_code, dimension_id, rater_pair, title, source, source_type, citation, evidence_certainty, study_count, sample_size, association_value, limitation, version)
SELECT
    'EVD_ATTN_PARENT_TEACHER_001',
    d.id,
    'PARENT_TEACHER',
    'Parent-Teacher discrepancy in attention ratings predicts multi-setting support needs',
    'Synthetic research record — replace with curated study',
    'SYSTEMATIC_REVIEW',
    'MindLens MVP Synthetic Citation, 2024',
    'VERY_LOW', 3, 1200,
    'Moderate correlation (r=0.42)',
    'Synthetic data used for hackathon prototype. Replace with validated research.',
    '1.0'
FROM dimensions d WHERE d.dimension_code = 'attention_persistence'
ON CONFLICT (evidence_code) DO NOTHING;

INSERT INTO evidence (evidence_code, dimension_id, rater_pair, title, source, source_type, citation, evidence_certainty, study_count, sample_size, association_value, limitation, version)
SELECT
    'EVD_ADAPT_ADOLESCENT_DISCREPANCY_001',
    d.id,
    'ADOLESCENT_TEACHER',
    'Adolescent self-report of adaptability diverges from adult ratings in transition periods',
    'Synthetic research record — replace with curated study',
    'META_ANALYSIS',
    'MindLens MVP Synthetic Citation, 2024',
    'VERY_LOW', 2, 400,
    'Small effect size (d=0.31)',
    'Synthetic data used for hackathon prototype. Replace with validated research.',
    '1.0'
FROM dimensions d WHERE d.dimension_code = 'adaptability'
ON CONFLICT (evidence_code) DO NOTHING;

-- ============================================================
-- SIGNALS
-- ============================================================

CREATE TABLE signals (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID        NOT NULL
                    REFERENCES student_cases(id) ON DELETE CASCADE,
    discrepancy_id  UUID
                    REFERENCES discrepancies(id) ON DELETE SET NULL,

    dimension_id    UUID        NOT NULL
                    REFERENCES dimensions(id) ON DELETE RESTRICT,

    title           VARCHAR(500) NOT NULL,
    description     TEXT        NOT NULL,
    signal_level    signal_level NOT NULL,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signals_case
    ON signals(case_id);

CREATE INDEX idx_signals_case_level
    ON signals(case_id, signal_level);

-- ============================================================
-- SIGNAL <-> EVIDENCE
-- ============================================================

CREATE TABLE signal_evidence (
    signal_id   UUID NOT NULL
                REFERENCES signals(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL
                REFERENCES evidence(id) ON DELETE RESTRICT,

    PRIMARY KEY (signal_id, evidence_id)
);

-- ============================================================
-- LIFESTYLE SIGNALS
-- ============================================================

CREATE TABLE lifestyle_signals (
    id                  UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID    NOT NULL
                        REFERENCES student_cases(id) ON DELETE CASCADE,

    factor              VARCHAR(255) NOT NULL,
    observed_response   JSONB   NOT NULL,

    evidence_id         UUID
                        REFERENCES evidence(id) ON DELETE RESTRICT,

    association_value   TEXT,
    certainty           VARCHAR(100),
    limitation          TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lifestyle_signals_case
    ON lifestyle_signals(case_id);

-- ============================================================
-- COUNSELOR REVIEWS
-- ============================================================

CREATE TABLE counselor_reviews (
    id              UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID                NOT NULL
                    REFERENCES student_cases(id) ON DELETE CASCADE,
    counselor_id    UUID                NOT NULL
                    REFERENCES users(id) ON DELETE RESTRICT,

    action          counselor_action    NOT NULL,
    note            TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_counselor_reviews_case
    ON counselor_reviews(case_id);

CREATE INDEX idx_counselor_reviews_counselor
    ON counselor_reviews(counselor_id);

-- ============================================================
-- AUDIT EVENTS
-- ============================================================

CREATE TABLE audit_events (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id     UUID
                REFERENCES student_cases(id) ON DELETE SET NULL,

    actor_type  actor_type  NOT NULL,
    actor_id    UUID,

    event_type  VARCHAR(100) NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',

    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_case_created
    ON audit_events(case_id, created_at DESC);

CREATE INDEX idx_audit_events_event_type
    ON audit_events(event_type);

-- ============================================================
-- CASE <-> COUNSELOR ASSIGNMENT
-- ============================================================

CREATE TABLE case_assignments (
    case_id         UUID NOT NULL
                    REFERENCES student_cases(id) ON DELETE CASCADE,
    counselor_id    UUID NOT NULL
                    REFERENCES users(id) ON DELETE RESTRICT,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (case_id, counselor_id)
);

CREATE INDEX idx_case_assignments_counselor
    ON case_assignments(counselor_id);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_student_cases_updated_at
    BEFORE UPDATE ON student_cases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_responses_updated_at
    BEFORE UPDATE ON responses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_counselor_reviews_updated_at
    BEFORE UPDATE ON counselor_reviews
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- READ MODEL / VIEW FOR THE COUNSELOR HEATMAP
-- ============================================================

CREATE VIEW counselor_dimension_comparison AS
SELECT
    ds.case_id,
    d.dimension_code,
    d.label         AS dimension,
    MAX(ds.score) FILTER (WHERE ds.rater_type = 'PARENT')      AS parent_score,
    MAX(ds.score) FILTER (WHERE ds.rater_type = 'TEACHER')     AS teacher_score,
    MAX(ds.score) FILTER (WHERE ds.rater_type = 'ADOLESCENT')  AS adolescent_score
FROM dimension_scores ds
JOIN dimensions d ON d.id = ds.dimension_id
GROUP BY
    ds.case_id,
    d.dimension_code,
    d.label;

-- ============================================================
-- SEED SYNTHETIC DEMO DATA
-- ============================================================

-- Seed org
INSERT INTO organizations (id, name) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Greenwood School District')
ON CONFLICT DO NOTHING;

-- Seed counselor (password: MindLens2024!)
INSERT INTO users (id, organization_id, name, email, password_hash, role) VALUES
    ('00000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000001',
     'Dr. Sarah Chen',
     'sarah.chen@greenwood.edu',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewzTY9KiNfeSMqBe',
     'COUNSELOR')
ON CONFLICT DO NOTHING;

-- ============================================================
-- IMPORTANT DESIGN CONSTRAINT
-- ============================================================
-- There is intentionally NO table/column such as:
--     overall_risk_score
--     self_harm_probability
--     clinical_diagnosis
--
-- MindLens stores:
--     multi-rater responses
--     deterministic dimension scores
--     pairwise discrepancies
--     evidence
--     contextual lifestyle signals
--     counselor decisions
--
-- The counselor, not the backend, makes the final interpretation/action.
