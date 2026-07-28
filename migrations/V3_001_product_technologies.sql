-- 1. Create technologies table
CREATE TABLE IF NOT EXISTS technologies (
    id BIGSERIAL PRIMARY KEY,
    plant_id BIGINT REFERENCES plants(id) ON DELETE CASCADE,
    operation_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_technologies_plant_op UNIQUE (plant_id, operation_name)
);

-- Enable Row Level Security (RLS) for technologies to match other plant-specific tables
ALTER TABLE technologies ENABLE ROW LEVEL SECURITY;

CREATE POLICY plant_isolation_technologies ON technologies
    FOR ALL
    USING (plant_id = current_setting('app.current_plant_id', true)::bigint)
    WITH CHECK (plant_id = current_setting('app.current_plant_id', true)::bigint);

-- Create index on plant_id for technologies
CREATE INDEX IF NOT EXISTS idx_technologies_plant ON technologies(plant_id);


-- 2. Create product_technology_mappings table
CREATE TABLE IF NOT EXISTS product_technology_mappings (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    technology_id BIGINT NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_technology UNIQUE (product_id, technology_id)
);

CREATE INDEX IF NOT EXISTS ix_product_technology_mappings_product_id ON product_technology_mappings(product_id);
CREATE INDEX IF NOT EXISTS ix_product_technology_mappings_technology_id ON product_technology_mappings(technology_id);


-- 3. Alter flowchart_steps to use technology_id instead of manufacturing_operation_id
DROP INDEX IF EXISTS idx_flowchart_steps_mfg_op;

ALTER TABLE flowchart_steps DROP COLUMN IF EXISTS manufacturing_operation_id CASCADE;
ALTER TABLE flowchart_steps DROP COLUMN IF EXISTS step_sequence CASCADE;
ALTER TABLE flowchart_steps DROP COLUMN IF EXISTS step_name CASCADE;

ALTER TABLE flowchart_steps ADD COLUMN IF NOT EXISTS technology_id BIGINT REFERENCES technologies(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_flowchart_steps_technology_id ON flowchart_steps(technology_id);
