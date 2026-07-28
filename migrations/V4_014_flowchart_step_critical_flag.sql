-- Add critical_flag column to flowchart_steps
ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS critical_flag VARCHAR NOT NULL DEFAULT 'none';
