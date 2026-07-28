CREATE TABLE IF NOT EXISTS measurement_units (
    id BIGSERIAL PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    symbology VARCHAR(50) NOT NULL,
    magnitude VARCHAR(255) NOT NULL
);

ALTER TABLE product_parameters ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE product_parameters ADD COLUMN IF NOT EXISTS measurement_unit_id BIGINT;
ALTER TABLE product_parameters ADD CONSTRAINT fk_product_parameters_measurement_unit FOREIGN KEY (measurement_unit_id) REFERENCES measurement_units (id) ON DELETE SET NULL;
ALTER TABLE product_parameters DROP COLUMN IF EXISTS unit;
