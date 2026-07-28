ALTER TABLE pfmea_worksheet_rows
ADD COLUMN IF NOT EXISTS work_element_process TEXT;

COMMENT ON COLUMN pfmea_worksheet_rows.work_element_process IS 'Step 2: Work Element Process (4M)';
