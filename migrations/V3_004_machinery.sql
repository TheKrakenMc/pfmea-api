CREATE TABLE IF NOT EXISTS pfmea.machinery (
    id BIGSERIAL PRIMARY KEY,
    machinery_name VARCHAR(255) NOT NULL,
    machinery_code VARCHAR(100) NOT NULL,
    plant_id BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    deleted_by BIGINT DEFAULT NULL REFERENCES pfmea.users(id),
    CONSTRAINT fk_machinery_plant FOREIGN KEY (plant_id) REFERENCES pfmea.plants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_machinery_plant_id ON pfmea.machinery(plant_id);
CREATE INDEX IF NOT EXISTS idx_machinery_code ON pfmea.machinery(machinery_code);
CREATE INDEX IF NOT EXISTS idx_machinery_active ON pfmea.machinery(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_machinery_deleted_by ON pfmea.machinery(deleted_by) WHERE deleted_by IS NOT NULL;
