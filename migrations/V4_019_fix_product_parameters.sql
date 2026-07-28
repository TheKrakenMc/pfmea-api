ALTER TABLE product_parameters 
DROP COLUMN IF EXISTS unit;

ALTER TABLE product_parameters 
ADD COLUMN IF NOT EXISTS measurement_unit_id BIGINT,
ADD COLUMN IF NOT EXISTS order_index INTEGER NOT NULL DEFAULT 0;

ALTER TABLE product_parameters
ADD CONSTRAINT fk_product_parameters_measurement_unit_id 
FOREIGN KEY (measurement_unit_id) REFERENCES measurement_units(id) ON DELETE SET NULL;
