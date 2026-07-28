CREATE TABLE IF NOT EXISTS pfmea.product_families (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_product_families_name ON pfmea.product_families(name);

-- Add the new column
ALTER TABLE pfmea.pfmea_headers ADD COLUMN product_family_id BIGINT;

-- Migrate existing data by creating product families from existing strings
INSERT INTO pfmea.product_families (name)
SELECT DISTINCT product_family 
FROM pfmea.pfmea_headers 
WHERE product_family IS NOT NULL AND product_family != ''
ON CONFLICT (name) DO NOTHING;

UPDATE pfmea.pfmea_headers ph
SET product_family_id = pf.id
FROM pfmea.product_families pf
WHERE ph.product_family = pf.name;

-- Drop the old column
ALTER TABLE pfmea.pfmea_headers DROP COLUMN product_family;

-- Add foreign key constraint
ALTER TABLE pfmea.pfmea_headers 
    ADD CONSTRAINT fk_pfmea_headers_product_family 
    FOREIGN KEY (product_family_id) REFERENCES pfmea.product_families(id) ON DELETE SET NULL;
