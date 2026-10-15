DO $$ DECLARE c record; BEGIN
 FOR c IN SELECT conname FROM pg_constraint WHERE conrelid='pfmea.flowchart_steps'::regclass AND contype='u' LOOP
  IF pg_get_constraintdef((SELECT oid FROM pg_constraint WHERE conrelid='pfmea.flowchart_steps'::regclass AND conname=c.conname)) LIKE '%flowchart_id%step_number%' THEN
   EXECUTE format('ALTER TABLE pfmea.flowchart_steps DROP CONSTRAINT %I',c.conname);
  END IF;
 END LOOP;
END $$;
ALTER TABLE flowchart_steps ADD CONSTRAINT uq_flowchart_step_key UNIQUE(flowchart_id,step_number,sub_step) DEFERRABLE INITIALLY DEFERRED;
