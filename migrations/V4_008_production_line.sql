CREATE TABLE IF NOT EXISTS pfmea.production_lines (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_production_lines_name ON pfmea.production_lines(name);

-- Add the new column
ALTER TABLE pfmea.pfmea_headers ADD COLUMN production_line_id BIGINT;

-- Migrate existing data by creating production lines from existing strings
INSERT INTO pfmea.production_lines (name)
SELECT DISTINCT production_line 
FROM pfmea.pfmea_headers 
WHERE production_line IS NOT NULL AND production_line != ''
ON CONFLICT (name) DO NOTHING;

UPDATE pfmea.pfmea_headers ph
SET production_line_id = pl.id
FROM pfmea.production_lines pl
WHERE ph.production_line = pl.name;

-- Drop the old column
ALTER TABLE pfmea.pfmea_headers DROP COLUMN production_line;

-- Add foreign key constraint
ALTER TABLE pfmea.pfmea_headers 
    ADD CONSTRAINT fk_pfmea_headers_production_line 
    FOREIGN KEY (production_line_id) REFERENCES pfmea.production_lines(id) ON DELETE SET NULL;
