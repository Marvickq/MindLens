-- MindLens migration 003
-- Research-configuration-driven discrepancy engine.
--
-- 1. Adds provenance columns to the existing `discrepancies` and `signals`
--    tables (idempotent — safe to run multiple times on live/remote DBs).
-- 2. Creates the `discrepancy_method_configs` table that holds the
--    research-derived comparison parameters.
--
-- NOTE: This file does NOT seed any reliability / SD / threshold values.
-- No fabricated or fallback research parameters are inserted. The engine
-- stays `unvalidated` until a real, validated research config is loaded.

-- ============================================================
-- DISCREPANCY METHOD CONFIG
-- ============================================================

CREATE TABLE IF NOT EXISTS discrepancy_method_configs (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_version      VARCHAR(50)     NOT NULL,
    dimension_id            UUID            NOT NULL
                            REFERENCES dimensions(id) ON DELETE RESTRICT,
    rater_pair              VARCHAR(50)     NOT NULL,
    methodology             VARCHAR(50)     NOT NULL DEFAULT 'sed',
    calculation_method      VARCHAR(100)    NOT NULL,
    calculation_version     VARCHAR(50)     NOT NULL,
    reliability             NUMERIC(10, 6),
    reliability_source      TEXT,
    reference_sd            NUMERIC(10, 6),
    reference_sd_source     TEXT,
    significance_threshold  NUMERIC(14, 6),
    source_citation         TEXT,
    interpretation_model    VARCHAR(50)     NOT NULL DEFAULT 'operations_triad',
    is_active               BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_config_instrument_dim_pair
        UNIQUE (instrument_version, dimension_id, rater_pair)
);

CREATE INDEX IF NOT EXISTS idx_config_dim_pair
    ON discrepancy_method_configs(dimension_id, rater_pair);

-- ============================================================
-- DISCREPANCIES — provenance columns
-- ============================================================

ALTER TABLE discrepancies
    ADD COLUMN IF NOT EXISTS reference_sed          NUMERIC(14, 6),
    ADD COLUMN IF NOT EXISTS interpretation_model    VARCHAR(50)  NOT NULL DEFAULT 'operations_triad',
    ADD COLUMN IF NOT EXISTS instrument_version      VARCHAR(50),
    ADD COLUMN IF NOT EXISTS rater_pair              VARCHAR(50),
    ADD COLUMN IF NOT EXISTS reliability_source      TEXT,
    ADD COLUMN IF NOT EXISTS reference_source        TEXT,
    ADD COLUMN IF NOT EXISTS status                  VARCHAR(20)  NOT NULL DEFAULT 'unvalidated';

-- ============================================================
-- SIGNALS — provenance columns
-- ============================================================

ALTER TABLE signals
    ADD COLUMN IF NOT EXISTS interpretation_model    VARCHAR(50)  NOT NULL DEFAULT 'operations_triad',
    ADD COLUMN IF NOT EXISTS instrument_version      VARCHAR(50),
    ADD COLUMN IF NOT EXISTS rater_pair              VARCHAR(50),
    ADD COLUMN IF NOT EXISTS status                  VARCHAR(20)  NOT NULL DEFAULT 'unvalidated';
