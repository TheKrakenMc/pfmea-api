-- Migration: Create technology_parameters table
-- Links critical process parameters to their parent technology/operation.

CREATE TABLE IF NOT EXISTS technology_parameters (
    id          BIGSERIAL PRIMARY KEY,
    technology_id BIGINT NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    unit        VARCHAR(50),
    target_value DOUBLE PRECISION,
    min_value    DOUBLE PRECISION,
    max_value    DOUBLE PRECISION,
    is_critical  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP WITH TIME ZONE
);

-- Index for fast lookup by technology
CREATE INDEX IF NOT EXISTS ix_technology_parameters_technology_id
    ON technology_parameters (technology_id);

-- Index for active parameters filtering
CREATE INDEX IF NOT EXISTS ix_technology_parameters_active
    ON technology_parameters (technology_id, is_active)
    WHERE is_active = TRUE;
