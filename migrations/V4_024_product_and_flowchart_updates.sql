-- Add new columns to products
ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS product_family_id BIGINT;
ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS production_line_id BIGINT;

-- Add foreign key constraints to products
ALTER TABLE pfmea.products 
    ADD CONSTRAINT fk_products_product_family 
    FOREIGN KEY (product_family_id) REFERENCES pfmea.product_families(id) ON DELETE SET NULL;

ALTER TABLE pfmea.products 
    ADD CONSTRAINT fk_products_production_line 
    FOREIGN KEY (production_line_id) REFERENCES pfmea.production_lines(id) ON DELETE SET NULL;

-- Add confidentiality_level to flowcharts and pfmea_headers
ALTER TABLE pfmea.flowcharts ADD COLUMN IF NOT EXISTS confidentiality_level VARCHAR;
ALTER TABLE pfmea.pfmea_headers ADD COLUMN IF NOT EXISTS confidentiality_level VARCHAR;
