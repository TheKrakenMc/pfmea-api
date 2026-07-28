-- Add symbol_type to flowchart_steps
ALTER TABLE flowchart_steps 
ADD COLUMN symbol_type VARCHAR NOT NULL DEFAULT 'operation';
