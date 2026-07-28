-- ============================================================================
-- PFMEA v2 — Migration 004: Centralized Document Versions (Polymorphic)
-- ============================================================================
-- Replaces individual *_revisions tables with a single polymorphic table.
-- Migrates existing data, then deprecates (but does NOT drop) old tables.
-- ============================================================================

BEGIN;

SAVEPOINT sp_document_versions;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. CREATE POLYMORPHIC TABLE
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE document_versions (
    id                      bigserial       PRIMARY KEY,
    document_type           varchar         NOT NULL,   -- 'flowchart', 'control_plan', 'operation_instruction'
    document_id             bigint          NOT NULL,
    revision_number         int             NOT NULL,
    change_reason           varchar         NOT NULL,
    created_by              bigint          NOT NULL REFERENCES users(id),
    created_at              timestamptz     DEFAULT now(),
    original_creation_date  timestamptz     NOT NULL,
    observations            text,
    snapshot_data           jsonb,                      -- full state snapshot at revision time
    is_initial_revision     boolean         DEFAULT false,

    CONSTRAINT uq_doc_version UNIQUE (document_type, document_id, revision_number)
);

-- Indexes
CREATE INDEX idx_doc_versions_type_id
    ON document_versions(document_type, document_id);
CREATE INDEX idx_doc_versions_created_at
    ON document_versions(created_at);
CREATE INDEX idx_doc_versions_created_by
    ON document_versions(created_by);

-- ────────────────────────────────────────────────────────────────────────────
-- 2. MIGRATE EXISTING DATA from flowchart_revisions
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO document_versions (
    document_type, document_id, revision_number, change_reason,
    created_by, created_at, original_creation_date, observations,
    is_initial_revision
)
SELECT
    'flowchart',
    flowchart_id,
    revision_number,
    change_reason,
    created_by,
    created_at,
    original_creation_date,
    observations,
    COALESCE(is_initial_revision, false)
FROM flowchart_revisions;

-- ────────────────────────────────────────────────────────────────────────────
-- 3. MIGRATE EXISTING DATA from control_plan_revisions
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO document_versions (
    document_type, document_id, revision_number, change_reason,
    created_by, created_at, original_creation_date, observations
)
SELECT
    'control_plan',
    control_plan_id,
    revision_number,
    change_reason,
    created_by,
    created_at,
    original_creation_date,
    observations
FROM control_plan_revisions;

-- ────────────────────────────────────────────────────────────────────────────
-- 4. MIGRATE EXISTING DATA from operation_instruction_revisions
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO document_versions (
    document_type, document_id, revision_number, change_reason,
    created_by, created_at, original_creation_date, observations
)
SELECT
    'operation_instruction',
    operation_instruction_sheet_id,
    revision_number,
    change_reason,
    created_by,
    created_at,
    original_creation_date,
    observations
FROM operation_instruction_revisions;

-- ────────────────────────────────────────────────────────────────────────────
-- 5. DEPRECATE OLD TABLES (rename, do NOT drop for safety)
-- ────────────────────────────────────────────────────────────────────────────

ALTER TABLE flowchart_revisions              RENAME TO _deprecated_flowchart_revisions;
ALTER TABLE control_plan_revisions           RENAME TO _deprecated_control_plan_revisions;
ALTER TABLE operation_instruction_revisions  RENAME TO _deprecated_operation_instruction_revisions;

COMMENT ON TABLE _deprecated_flowchart_revisions
    IS 'DEPRECATED in v2 — data migrated to document_versions. Safe to drop after verification.';
COMMENT ON TABLE _deprecated_control_plan_revisions
    IS 'DEPRECATED in v2 — data migrated to document_versions. Safe to drop after verification.';
COMMENT ON TABLE _deprecated_operation_instruction_revisions
    IS 'DEPRECATED in v2 — data migrated to document_versions. Safe to drop after verification.';

RELEASE SAVEPOINT sp_document_versions;

COMMIT;
