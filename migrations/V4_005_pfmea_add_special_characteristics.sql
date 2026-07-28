-- Add special_characteristics to pfmea_worksheet_rows table
ALTER TABLE pfmea.pfmea_worksheet_rows ADD COLUMN IF NOT EXISTS special_characteristics TEXT;
