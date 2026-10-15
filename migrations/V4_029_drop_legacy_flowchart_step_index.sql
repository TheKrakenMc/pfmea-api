-- Migration V4_029_drop_legacy_flowchart_step_index.sql
-- Drop legacy unique index on (flowchart_id, step_number) so sub-steps (e.g., 10.0, 10.1) are allowed.

DROP INDEX IF EXISTS pfmea.flowchart_steps_flowchart_id_step_number_idx;
