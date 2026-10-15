-- Migration: Add optional fields for APG corporate layout
-- This script is idempotent and can be applied on existing databases.

ALTER TABLE pfmea.pfmea_headers
    ADD COLUMN IF NOT EXISTS supplier_part_number TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS model_year TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS key_date DATE DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS special_document_control TEXT DEFAULT '0',
    ADD COLUMN IF NOT EXISTS process_responsibility TEXT DEFAULT NULL;
