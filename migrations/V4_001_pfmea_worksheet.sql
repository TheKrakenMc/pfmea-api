-- ============================================================================
-- V4_001_pfmea_worksheet.sql
-- PFMEA Worksheet Module (AIAG-VDA 2019 Steps 1–6)
-- Extends pfmea_headers, pfmea_team_members; creates pfmea_worksheet_rows.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 0. Schema Alignments (pfmea_projects -> pfmea_headers)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    -- Rename table if old name exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'pfmea' AND table_name = 'pfmea_projects') THEN
        ALTER TABLE pfmea_projects RENAME TO pfmea_headers;
    END IF;

    -- Rename columns in pfmea_headers
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'pfmea_headers' AND column_name = 'pfmea_code') THEN
        ALTER TABLE pfmea_headers RENAME COLUMN pfmea_code TO pfmea_id_number;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'pfmea_headers' AND column_name = 'last_revision_date') THEN
        ALTER TABLE pfmea_headers RENAME COLUMN last_revision_date TO revision_date;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'pfmea_headers' AND column_name = 'title') THEN
        ALTER TABLE pfmea_headers RENAME COLUMN title TO project_name;
        ALTER TABLE pfmea_headers ALTER COLUMN project_name DROP NOT NULL;
    END IF;

    -- Rename foreign keys in referencing tables
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'pfmea_team_members' AND column_name = 'pfmea_project_id') THEN
        ALTER TABLE pfmea_team_members RENAME COLUMN pfmea_project_id TO pfmea_id;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'process_items' AND column_name = 'pfmea_project_id') THEN
        ALTER TABLE process_items RENAME COLUMN pfmea_project_id TO pfmea_id;
    END IF;
END$$;

-- ---------------------------------------------------------------------------
-- 1. Extend pfmea_headers (Step 1 — Global Header)
-- ---------------------------------------------------------------------------
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS project_name TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS customer TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS original_launch_date DATE;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS moc_status TEXT NOT NULL DEFAULT 'Draft';
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS part_number TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS product_description TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS product_family TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS production_line TEXT;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS plant_id BIGINT REFERENCES plants(id);

-- Add CHECK constraint for moc_status (wrapped in DO block for idempotency)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_pfmea_headers_moc_status'
    ) THEN
        ALTER TABLE pfmea_headers
            ADD CONSTRAINT ck_pfmea_headers_moc_status
            CHECK (moc_status IN ('Draft', 'Submitted for Review', 'Approved', 'Archived'));
    END IF;
END$$;

-- Index on plant_id for multi-plant filtering
CREATE INDEX IF NOT EXISTS ix_pfmea_headers_plant_id ON pfmea_headers(plant_id);

-- ---------------------------------------------------------------------------
-- 2. Extend pfmea_team_members (Core Team role assignment)
-- ---------------------------------------------------------------------------
ALTER TABLE pfmea_team_members ADD COLUMN IF NOT EXISTS role_in_team TEXT NOT NULL DEFAULT 'Team Member';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_pfmea_team_role_in_team'
    ) THEN
        ALTER TABLE pfmea_team_members
            ADD CONSTRAINT ck_pfmea_team_role_in_team
            CHECK (role_in_team IN ('PFMEA Owner', 'Team Member', 'Viewer'));
    END IF;
END$$;

-- ---------------------------------------------------------------------------
-- 3. Create pfmea_worksheet_rows (Steps 2–6 flat table)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pfmea_worksheet_rows (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pfmea_id BIGINT NOT NULL REFERENCES pfmea_headers(id) ON DELETE CASCADE,
    flowchart_step_id BIGINT REFERENCES flowchart_steps(id) ON DELETE SET NULL,

    -- Step 2: Structure Analysis (inherited from flowchart)
    process_item_name TEXT,
    station_operation TEXT,
    operation_type TEXT,

    -- Step 3: Function Analysis
    function_step TEXT,

    -- Step 4: Failure Analysis
    failure_mode TEXT,
    failure_effect TEXT,
    severity INTEGER CHECK (severity BETWEEN 1 AND 10),
    failure_cause TEXT,
    occurrence INTEGER CHECK (occurrence BETWEEN 1 AND 10),

    -- Step 5: Risk Analysis (Current Controls)
    prevention_controls TEXT,
    detection_controls TEXT,
    detection INTEGER CHECK (detection BETWEEN 1 AND 10),
    action_priority TEXT CHECK (action_priority IN ('H', 'M', 'L')),

    -- Step 6: Optimization
    optimization_prevention_action TEXT,
    optimization_detection_action TEXT,
    responsible_person_id BIGINT REFERENCES users(id),
    target_completion_date DATE,
    action_status TEXT DEFAULT 'Open' CHECK (action_status IN ('Open', 'In Progress', 'Completed')),
    actions_taken TEXT,
    completion_date DATE,

    -- Re-evaluation (after optimization)
    new_severity INTEGER CHECK (new_severity BETWEEN 1 AND 10),
    new_occurrence INTEGER CHECK (new_occurrence BETWEEN 1 AND 10),
    new_detection INTEGER CHECK (new_detection BETWEEN 1 AND 10),
    new_action_priority TEXT CHECK (new_action_priority IN ('H', 'M', 'L')),

    -- Row ordering within the PFMEA
    sequence_order INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS ix_worksheet_rows_pfmea_id ON pfmea_worksheet_rows(pfmea_id);
CREATE INDEX IF NOT EXISTS ix_worksheet_rows_flowchart_step ON pfmea_worksheet_rows(flowchart_step_id);
CREATE INDEX IF NOT EXISTS ix_worksheet_rows_action_priority ON pfmea_worksheet_rows(action_priority);
CREATE INDEX IF NOT EXISTS ix_worksheet_rows_responsible ON pfmea_worksheet_rows(responsible_person_id);
CREATE INDEX IF NOT EXISTS ix_worksheet_rows_action_status ON pfmea_worksheet_rows(action_status);

-- ---------------------------------------------------------------------------
-- 4. Extend document_audit_logs for field-level granularity
-- ---------------------------------------------------------------------------
ALTER TABLE document_audit_logs ADD COLUMN IF NOT EXISTS entity_type TEXT;
ALTER TABLE document_audit_logs ADD COLUMN IF NOT EXISTS entity_id BIGINT;
ALTER TABLE document_audit_logs ADD COLUMN IF NOT EXISTS field_name TEXT;
ALTER TABLE document_audit_logs ADD COLUMN IF NOT EXISTS old_value TEXT;
ALTER TABLE document_audit_logs ADD COLUMN IF NOT EXISTS new_value TEXT;

-- Composite index for entity-scoped audit queries
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity ON document_audit_logs(entity_type, entity_id);
