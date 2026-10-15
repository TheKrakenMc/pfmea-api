ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS source_reviewed boolean NOT NULL DEFAULT false;
ALTER TABLE control_plan_items ADD COLUMN IF NOT EXISTS source_review_reason text;
