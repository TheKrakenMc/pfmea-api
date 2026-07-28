-- V4_004_pfmea_split_failure_effect.sql
-- Split Step 4 Failure Effect into Plant, Customer, and End User

ALTER TABLE pfmea_worksheet_rows
ADD COLUMN failure_effect_plant TEXT,
ADD COLUMN failure_effect_customer TEXT,
ADD COLUMN failure_effect_end_user TEXT;

-- Migrate existing data from failure_effect to failure_effect_plant (assuming it relates to plant mostly)
UPDATE pfmea_worksheet_rows
SET failure_effect_plant = failure_effect;

-- Drop old column
ALTER TABLE pfmea_worksheet_rows
DROP COLUMN failure_effect;
