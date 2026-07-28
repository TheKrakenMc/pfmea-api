-- V4_003_pfmea_step3_columns.sql
-- Add Step 3 columns to pfmea_worksheet_rows for AIAG-VDA compatibility

ALTER TABLE pfmea_worksheet_rows
ADD COLUMN function_process_item_plant TEXT,
ADD COLUMN function_process_item_customer TEXT,
ADD COLUMN function_process_item_end_user TEXT,
ADD COLUMN function_process_step TEXT,
ADD COLUMN function_work_element TEXT;

-- Migrate existing data from function_step to function_process_step
UPDATE pfmea_worksheet_rows
SET function_process_step = function_step;

-- Drop old column
ALTER TABLE pfmea_worksheet_rows
DROP COLUMN function_step;
