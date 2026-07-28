-- Replace unit string with measurement_unit_id foreign key in technology_parameters

ALTER TABLE technology_parameters
ADD COLUMN measurement_unit_id BIGINT;

ALTER TABLE technology_parameters
ADD CONSTRAINT fk_tech_params_unit
FOREIGN KEY (measurement_unit_id) REFERENCES measurement_units(id) ON DELETE SET NULL;

-- Note: We are dropping the 'unit' column but keeping the data requires mapping. 
-- For simplicity, since this is a new feature in development, we drop the unit column.
ALTER TABLE technology_parameters
DROP COLUMN unit;
