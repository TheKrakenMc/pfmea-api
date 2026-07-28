-- ============================================================================
-- PFMEA v2 — Migration 002: Soft Delete Universal
-- ============================================================================
-- Adds `deleted_at` (timestamptz) and `deleted_by` (bigint → users.id)
-- to every table that already has `is_active`.
-- Creates partial indexes WHERE deleted_at IS NULL for fast active-only queries.
-- ============================================================================

BEGIN;

SAVEPOINT sp_soft_delete;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. ADD COLUMNS
-- ────────────────────────────────────────────────────────────────────────────

-- roles
ALTER TABLE roles
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- regions
ALTER TABLE regions
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- plants
ALTER TABLE plants
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- users
ALTER TABLE users
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- customers
ALTER TABLE customers
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- products
ALTER TABLE products
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- manufacturing_locations
ALTER TABLE manufacturing_locations
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- manufacturing_operations
ALTER TABLE manufacturing_operations
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- flowcharts
ALTER TABLE flowcharts
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- control_plans
ALTER TABLE control_plans
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- operation_instruction_sheets
ALTER TABLE operation_instruction_sheets
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- technical_documents
ALTER TABLE technical_documents
    ADD COLUMN deleted_at  timestamptz DEFAULT NULL,
    ADD COLUMN deleted_by  bigint      DEFAULT NULL REFERENCES users(id);

-- ────────────────────────────────────────────────────────────────────────────
-- 2. PARTIAL INDEXES  (WHERE deleted_at IS NULL)
-- ────────────────────────────────────────────────────────────────────────────
-- These dramatically speed up queries that filter for active records only.

CREATE INDEX idx_roles_active
    ON roles(id) WHERE deleted_at IS NULL;

CREATE INDEX idx_regions_active
    ON regions(id) WHERE deleted_at IS NULL;

CREATE INDEX idx_plants_active
    ON plants(id, region_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_users_active
    ON users(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_customers_active
    ON customers(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_products_active
    ON products(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_manufacturing_locations_active
    ON manufacturing_locations(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_manufacturing_operations_active
    ON manufacturing_operations(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_flowcharts_active
    ON flowcharts(id, plant_id) WHERE deleted_at IS NULL;

CREATE INDEX idx_control_plans_active
    ON control_plans(id) WHERE deleted_at IS NULL;

CREATE INDEX idx_instruction_sheets_active
    ON operation_instruction_sheets(id) WHERE deleted_at IS NULL;

CREATE INDEX idx_technical_documents_active
    ON technical_documents(id, plant_id) WHERE deleted_at IS NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- 3. ADD deleted_by FK INDEXES (for reverse lookups)
-- ────────────────────────────────────────────────────────────────────────────

CREATE INDEX idx_roles_deleted_by              ON roles(deleted_by)              WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_regions_deleted_by            ON regions(deleted_by)            WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_plants_deleted_by             ON plants(deleted_by)             WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_users_deleted_by              ON users(deleted_by)              WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_customers_deleted_by          ON customers(deleted_by)          WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_products_deleted_by           ON products(deleted_by)           WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_mfg_locations_deleted_by      ON manufacturing_locations(deleted_by) WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_mfg_operations_deleted_by     ON manufacturing_operations(deleted_by) WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_flowcharts_deleted_by         ON flowcharts(deleted_by)         WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_control_plans_deleted_by      ON control_plans(deleted_by)      WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_instr_sheets_deleted_by       ON operation_instruction_sheets(deleted_by) WHERE deleted_by IS NOT NULL;
CREATE INDEX idx_tech_documents_deleted_by     ON technical_documents(deleted_by) WHERE deleted_by IS NOT NULL;

RELEASE SAVEPOINT sp_soft_delete;

COMMIT;
