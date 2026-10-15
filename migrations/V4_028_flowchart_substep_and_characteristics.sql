-- Migration V4_028_flowchart_substep_and_characteristics.sql
-- Add sub_step, product_characteristics, process_characteristics, and target to pfmea.flowchart_steps.

ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS sub_step INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS product_characteristics TEXT;
ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS process_characteristics TEXT;
ALTER TABLE pfmea.flowchart_steps ADD COLUMN IF NOT EXISTS target TEXT;

-- Copy legacy data if present
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'pfmea' AND table_name = 'flowchart_steps' AND column_name = 'product_characteristic'
    ) THEN
        UPDATE pfmea.flowchart_steps 
        SET product_characteristics = product_characteristic 
        WHERE product_characteristics IS NULL AND product_characteristic IS NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'pfmea' AND table_name = 'flowchart_steps' AND column_name = 'process_characteristic'
    ) THEN
        UPDATE pfmea.flowchart_steps 
        SET process_characteristics = process_characteristic 
        WHERE process_characteristics IS NULL AND process_characteristic IS NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'pfmea' AND table_name = 'flowchart_steps' AND column_name = 'target_spec'
    ) THEN
        UPDATE pfmea.flowchart_steps 
        SET target = target_spec 
        WHERE target IS NULL AND target_spec IS NOT NULL;
    END IF;
END $$;

-- Drop old unique constraint if present
ALTER TABLE pfmea.flowchart_steps DROP CONSTRAINT IF EXISTS uq_flowchart_steps_fc_step;

-- Add new composite unique constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_flowchart_steps_fc_step_sub'
    ) THEN
        ALTER TABLE pfmea.flowchart_steps 
        ADD CONSTRAINT uq_flowchart_steps_fc_step_sub 
        UNIQUE (flowchart_id, step_number, sub_step);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_flowchart_steps_ordering 
ON pfmea.flowchart_steps (flowchart_id, step_number, sub_step);
