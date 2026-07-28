CREATE TABLE IF NOT EXISTS technology_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_technology_categories_name UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS ix_technology_categories_name ON technology_categories (name);
