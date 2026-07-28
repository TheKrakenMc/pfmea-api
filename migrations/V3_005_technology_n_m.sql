-- Migration V3_005_technology_n_m.sql
-- Add many-to-many relationship between plants and technologies
-- Add code column to technologies

SET search_path TO pfmea, public;

-- 1. Create junction table
CREATE TABLE IF NOT EXISTS plant_technologies (
    plant_id BIGINT NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    technology_id BIGINT NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    PRIMARY KEY (plant_id, technology_id)
);

-- 2. Migrate existing data
INSERT INTO plant_technologies (plant_id, technology_id)
SELECT plant_id, id FROM technologies WHERE plant_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- 3. Add code column
ALTER TABLE technologies ADD COLUMN IF NOT EXISTS code VARCHAR(50);

-- Assign temporary unique codes to existing rows
UPDATE technologies SET code = 'OLD-' || id::text WHERE code IS NULL;

-- Make code NOT NULL and UNIQUE
ALTER TABLE technologies ALTER COLUMN code SET NOT NULL;
ALTER TABLE technologies DROP CONSTRAINT IF EXISTS uq_technologies_code;
ALTER TABLE technologies ADD CONSTRAINT uq_technologies_code UNIQUE (code);
CREATE INDEX IF NOT EXISTS ix_technologies_code ON technologies(code);

-- 4. Drop old constraints and columns
ALTER TABLE technologies DROP CONSTRAINT IF EXISTS uq_technologies_plant_name;
ALTER TABLE technologies DROP COLUMN IF EXISTS plant_id CASCADE;
