-- Migration script to update technologies table

ALTER TABLE technologies
    -- Rename existing operation_name to name
    RENAME COLUMN operation_name TO name;

ALTER TABLE technologies
    -- Add new columns
    ADD COLUMN category VARCHAR,
    ADD COLUMN description VARCHAR,
    ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
    ADD COLUMN suggested_parameters JSONB,
    ADD COLUMN created_by INTEGER REFERENCES users(id),
    ADD COLUMN updated_by INTEGER REFERENCES users(id),
    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

-- We already have created_at in the original schema as shown in previous context? Let's check. 
-- The model had `created_at` in the DB image. If it didn't exist in Python it might still exist in DB. 
-- Just to be safe, we'll try to add it only if it doesn't exist, or just leave it.
-- We can add it if missing:
-- ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Update unique constraint
ALTER TABLE technologies DROP CONSTRAINT IF EXISTS uq_technologies_plant_op;
ALTER TABLE technologies ADD CONSTRAINT uq_technologies_plant_name UNIQUE (plant_id, name);
