-- ============================================================================
-- PFMEA v2 — Migration 005: Multi-Plant RLS + Compound Indexes
-- ============================================================================
-- 1. Creates compound indexes with plant_id for critical query paths.
-- 2. Enables Row Level Security on key tables.
-- 3. Creates isolation policies by plant_id.
-- ============================================================================

BEGIN;

SAVEPOINT sp_multi_plant_rls;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. COMPOUND INDEXES WITH plant_id
-- ────────────────────────────────────────────────────────────────────────────

-- Flowcharts — most common query pattern: filter by plant + status
CREATE INDEX IF NOT EXISTS idx_flowcharts_plant_status
    ON flowcharts(plant_id, status) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_flowcharts_plant_product
    ON flowcharts(plant_id, product_id) WHERE deleted_at IS NULL;

-- Products — lookup by plant + part_number
CREATE INDEX IF NOT EXISTS idx_products_plant_part
    ON products(plant_id, part_number) WHERE deleted_at IS NULL;

-- Users — lookup by plant
CREATE INDEX IF NOT EXISTS idx_users_plant_role
    ON users(plant_id, role_id) WHERE deleted_at IS NULL;

-- Customers — lookup by plant
CREATE INDEX IF NOT EXISTS idx_customers_plant_status
    ON customers(plant_id, status) WHERE deleted_at IS NULL;

-- PFMEA Projects — filter by plant + status
CREATE INDEX IF NOT EXISTS idx_pfmea_projects_plant_status
    ON pfmea_projects(plant_id, status);

-- Manufacturing Locations — by plant
CREATE INDEX IF NOT EXISTS idx_mfg_locations_plant
    ON manufacturing_locations(plant_id) WHERE deleted_at IS NULL;

-- Manufacturing Operations — by plant
CREATE INDEX IF NOT EXISTS idx_mfg_operations_plant
    ON manufacturing_operations(plant_id) WHERE deleted_at IS NULL;

-- Technical Documents — by plant + status
CREATE INDEX IF NOT EXISTS idx_tech_docs_plant_status
    ON technical_documents(plant_id, status) WHERE deleted_at IS NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- 2. ENABLE ROW LEVEL SECURITY
-- ────────────────────────────────────────────────────────────────────────────
-- RLS is enforced per-session via:  SET app.current_plant_id = '<id>';
-- The application MUST set this at the beginning of every DB session.

ALTER TABLE flowcharts                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE products                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE pfmea_projects              ENABLE ROW LEVEL SECURITY;
ALTER TABLE manufacturing_locations     ENABLE ROW LEVEL SECURITY;
ALTER TABLE manufacturing_operations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE technical_documents         ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                       ENABLE ROW LEVEL SECURITY;

-- ────────────────────────────────────────────────────────────────────────────
-- 3. CREATE ROW-LEVEL POLICIES
-- ────────────────────────────────────────────────────────────────────────────
-- Each policy restricts SELECT/INSERT/UPDATE/DELETE to rows matching
-- the plant_id stored in the session variable app.current_plant_id.
-- Superusers and the table owner bypass RLS by default.

-- Flowcharts
CREATE POLICY plant_isolation_flowcharts ON flowcharts
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Products
CREATE POLICY plant_isolation_products ON products
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Customers
CREATE POLICY plant_isolation_customers ON customers
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- PFMEA Projects
CREATE POLICY plant_isolation_pfmea ON pfmea_projects
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Manufacturing Locations
CREATE POLICY plant_isolation_mfg_locations ON manufacturing_locations
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Manufacturing Operations
CREATE POLICY plant_isolation_mfg_operations ON manufacturing_operations
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Technical Documents
CREATE POLICY plant_isolation_tech_docs ON technical_documents
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Users
CREATE POLICY plant_isolation_users ON users
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- ────────────────────────────────────────────────────────────────────────────
-- 4. GRANT USAGE OF app.current_plant_id TO APPLICATION ROLE
-- ────────────────────────────────────────────────────────────────────────────
-- Note: The application connects as the DB user (e.g., 'pfmea_app').
-- If using the postgres superuser, RLS is bypassed unless FORCE ROW LEVEL
-- SECURITY is enabled. For testing, you can force RLS on superusers:

-- ALTER TABLE flowcharts FORCE ROW LEVEL SECURITY;
-- (uncomment for strict enforcement even as superuser)

RELEASE SAVEPOINT sp_multi_plant_rls;

COMMIT;
