ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS pfmea_worksheet_row_id bigint REFERENCES pfmea_worksheet_rows(id) ON DELETE SET NULL;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS source_row_id bigint;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS needs_review boolean NOT NULL DEFAULT false;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS characteristic text;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS classification varchar(2);
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS specification text;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS unit_id bigint REFERENCES measurement_units(id);
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS measurement_method text;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS sample_size integer;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS sample_frequency text;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS responsible_person_id bigint REFERENCES users(id);
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS reaction_plan text;
WITH candidates AS (
 SELECT i.id, min(r.id) AS row_id, count(*) AS n FROM control_plan_items i
 JOIN control_plans c ON c.id=i.control_plan_id
 JOIN pfmea_worksheet_rows r ON r.pfmea_id=c.pfmea_project_id
 AND i.item_name = 'Mode: ' || r.failure_mode || ' (Step: ' || r.station_operation || ')'
 GROUP BY i.id), unique_candidates AS (
 SELECT c.* FROM candidates c WHERE n=1 AND NOT EXISTS (
 SELECT 1 FROM candidates other WHERE other.id<>c.id AND other.row_id=c.row_id))
UPDATE control_plan_items i SET pfmea_worksheet_row_id=c.row_id, source_row_id=c.row_id FROM unique_candidates c WHERE i.id=c.id;
UPDATE control_plan_items SET needs_review=true WHERE pfmea_worksheet_row_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_control_plan_source ON control_plan_items(control_plan_id,pfmea_worksheet_row_id) WHERE pfmea_worksheet_row_id IS NOT NULL;
