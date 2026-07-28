-- Add custom_description column to flowchart_steps
ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS custom_description VARCHAR;
