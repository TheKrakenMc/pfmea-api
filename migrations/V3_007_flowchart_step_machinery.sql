-- 1. Add machinery_id to flowchart_steps
ALTER TABLE flowchart_steps ADD COLUMN IF NOT EXISTS machinery_id BIGINT REFERENCES machinery(id) ON DELETE SET NULL;

-- 2. Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_flowchart_steps_machinery_id ON flowchart_steps(machinery_id);
