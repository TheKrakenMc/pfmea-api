ALTER TABLE product_parameters
ADD COLUMN IF NOT EXISTS technology_id BIGINT;

ALTER TABLE product_parameters
ADD CONSTRAINT fk_product_parameters_technology_id
FOREIGN KEY (technology_id) REFERENCES technologies(id) ON DELETE SET NULL;
