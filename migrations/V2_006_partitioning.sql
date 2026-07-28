-- ============================================================================
-- PFMEA v2 — Migration 006: Table Partitioning
-- ============================================================================
-- Partitions high-growth tables by time range (quarterly).
-- 
-- Strategy:
--   1. Create new partitioned table with _v2 suffix
--   2. Copy existing data
--   3. Rename old → _legacy, new → original name
--   4. Create quarterly partitions for current + next year
-- ============================================================================

BEGIN;

SAVEPOINT sp_partitioning;

-- ════════════════════════════════════════════════════════════════════════════
-- A. DOCUMENT_AUDIT_LOGS — PARTITION BY RANGE (performed_at) QUARTERLY
-- ════════════════════════════════════════════════════════════════════════════

-- 1. Create partitioned table
CREATE TABLE document_audit_logs_v2 (
    id                              bigserial,
    flowchart_id                    bigint REFERENCES flowcharts(id),
    pfmea_project_id                bigint REFERENCES pfmea_projects(id),
    control_plan_id                 bigint REFERENCES control_plans(id),
    operation_instruction_sheet_id  bigint REFERENCES operation_instruction_sheets(id),
    action                          varchar NOT NULL,
    performed_by                    bigint  NOT NULL REFERENCES users(id),
    action_details                  text,
    previous_values                 jsonb,
    new_values                      jsonb,
    ip_address                      inet,
    user_agent                      varchar,
    request_id                      uuid,
    performed_at                    timestamptz DEFAULT now(),
    PRIMARY KEY (id, performed_at)
) PARTITION BY RANGE (performed_at);

-- 2. Create quarterly partitions (2026 Q1-Q4 + 2027 Q1-Q4)
CREATE TABLE document_audit_logs_2026_q1 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE document_audit_logs_2026_q2 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE document_audit_logs_2026_q3 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE document_audit_logs_2026_q4 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

CREATE TABLE document_audit_logs_2027_q1 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2027-01-01') TO ('2027-04-01');
CREATE TABLE document_audit_logs_2027_q2 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2027-04-01') TO ('2027-07-01');
CREATE TABLE document_audit_logs_2027_q3 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2027-07-01') TO ('2027-10-01');
CREATE TABLE document_audit_logs_2027_q4 PARTITION OF document_audit_logs_v2
    FOR VALUES FROM ('2027-10-01') TO ('2028-01-01');

-- 3. Recreate indexes on partitioned table
CREATE INDEX idx_audit_logs_v2_flowchart      ON document_audit_logs_v2(flowchart_id, performed_at);
CREATE INDEX idx_audit_logs_v2_pfmea          ON document_audit_logs_v2(pfmea_project_id, performed_at);
CREATE INDEX idx_audit_logs_v2_cp             ON document_audit_logs_v2(control_plan_id, performed_at);
CREATE INDEX idx_audit_logs_v2_ois            ON document_audit_logs_v2(operation_instruction_sheet_id, performed_at);
CREATE INDEX idx_audit_logs_v2_performed_by   ON document_audit_logs_v2(performed_by);
CREATE INDEX idx_audit_logs_v2_performed_at   ON document_audit_logs_v2(performed_at);
CREATE INDEX idx_audit_logs_v2_action         ON document_audit_logs_v2(action);
CREATE INDEX idx_audit_logs_v2_request_id     ON document_audit_logs_v2(request_id);

-- 4. Migrate existing data
INSERT INTO document_audit_logs_v2 (
    id, flowchart_id, pfmea_project_id, control_plan_id,
    operation_instruction_sheet_id, action, performed_by,
    action_details, previous_values, new_values, performed_at
)
SELECT
    id, flowchart_id, pfmea_project_id, control_plan_id,
    operation_instruction_sheet_id, action, performed_by,
    action_details, previous_values, new_values, performed_at
FROM document_audit_logs;

-- 5. Swap tables
ALTER TABLE document_audit_logs RENAME TO _legacy_document_audit_logs;
ALTER TABLE document_audit_logs_v2 RENAME TO document_audit_logs;

-- Reset sequence
SELECT setval(
    pg_get_serial_sequence('document_audit_logs', 'id'),
    COALESCE((SELECT MAX(id) FROM document_audit_logs), 0) + 1
);

-- ════════════════════════════════════════════════════════════════════════════
-- B. DOCUMENT_VERSIONS — PARTITION BY RANGE (created_at) QUARTERLY
-- ════════════════════════════════════════════════════════════════════════════
-- Note: This applies to the table created in V2_004.
-- We recreate it as partitioned. Since V2_004 just ran, minimal data exists.

-- Drop the non-partitioned version
ALTER TABLE document_versions RENAME TO _tmp_document_versions;

-- Create partitioned version
CREATE TABLE document_versions (
    id                      bigserial,
    document_type           varchar         NOT NULL,
    document_id             bigint          NOT NULL,
    revision_number         int             NOT NULL,
    change_reason           varchar         NOT NULL,
    created_by              bigint          NOT NULL REFERENCES users(id),
    created_at              timestamptz     DEFAULT now(),
    original_creation_date  timestamptz     NOT NULL,
    observations            text,
    snapshot_data           jsonb,
    is_initial_revision     boolean         DEFAULT false,
    PRIMARY KEY (id, created_at),
    CONSTRAINT uq_doc_version_part UNIQUE (document_type, document_id, revision_number, created_at)
) PARTITION BY RANGE (created_at);

-- Quarterly partitions
CREATE TABLE document_versions_2026_q1 PARTITION OF document_versions
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE document_versions_2026_q2 PARTITION OF document_versions
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE document_versions_2026_q3 PARTITION OF document_versions
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE document_versions_2026_q4 PARTITION OF document_versions
    FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

CREATE TABLE document_versions_2027_q1 PARTITION OF document_versions
    FOR VALUES FROM ('2027-01-01') TO ('2027-04-01');
CREATE TABLE document_versions_2027_q2 PARTITION OF document_versions
    FOR VALUES FROM ('2027-04-01') TO ('2027-07-01');
CREATE TABLE document_versions_2027_q3 PARTITION OF document_versions
    FOR VALUES FROM ('2027-07-01') TO ('2027-10-01');
CREATE TABLE document_versions_2027_q4 PARTITION OF document_versions
    FOR VALUES FROM ('2027-10-01') TO ('2028-01-01');

-- Indexes
CREATE INDEX idx_doc_versions_type_id_part    ON document_versions(document_type, document_id);
CREATE INDEX idx_doc_versions_created_at_part ON document_versions(created_at);
CREATE INDEX idx_doc_versions_created_by_part ON document_versions(created_by);

-- Migrate data from temporary table
INSERT INTO document_versions (
    id, document_type, document_id, revision_number, change_reason,
    created_by, created_at, original_creation_date, observations,
    snapshot_data, is_initial_revision
)
SELECT
    id, document_type, document_id, revision_number, change_reason,
    created_by, created_at, original_creation_date, observations,
    snapshot_data, is_initial_revision
FROM _tmp_document_versions;

-- Cleanup
DROP TABLE _tmp_document_versions;

-- Reset sequence
SELECT setval(
    pg_get_serial_sequence('document_versions', 'id'),
    COALESCE((SELECT MAX(id) FROM document_versions), 0) + 1
);

RELEASE SAVEPOINT sp_partitioning;

COMMIT;
