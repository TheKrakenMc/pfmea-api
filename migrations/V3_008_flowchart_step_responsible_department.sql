-- Add responsible_department to flowchart_steps with a default value of 'Producción'
ALTER TABLE flowchart_steps ADD COLUMN IF NOT EXISTS responsible_department VARCHAR(100) NOT NULL DEFAULT 'Producción';
