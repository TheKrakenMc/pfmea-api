-- The runtime database role MUST be NOSUPERUSER NOBYPASSRLS and not own tables.
CREATE OR REPLACE FUNCTION pfmea.authorized_plant(p bigint) RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT current_setting('app.is_admin',true)='true' OR (
 p = nullif(current_setting('app.current_plant_id',true),'')::bigint AND EXISTS (
 SELECT 1 FROM pfmea.user_plants u WHERE u.plant_id=p AND u.user_id=nullif(current_setting('app.current_user_id',true),'')::bigint));
$$;
CREATE OR REPLACE FUNCTION pfmea.authorized_pfmea(p bigint) RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT current_setting('app.is_admin',true)='true' OR EXISTS (
 SELECT 1 FROM pfmea.pfmea_headers h WHERE h.id=p AND pfmea.authorized_plant(h.plant_id) AND (
 h.owner_id=nullif(current_setting('app.current_user_id',true),'')::bigint OR EXISTS (
 SELECT 1 FROM pfmea.pfmea_team_members t WHERE t.pfmea_id=h.id AND t.user_id=nullif(current_setting('app.current_user_id',true),'')::bigint)));
$$;
DO $$ DECLARE t text; pol record; BEGIN
 FOREACH t IN ARRAY ARRAY['flowcharts','products','customers','manufacturing_locations','manufacturing_operations','technical_documents','technologies','machinery'] LOOP
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='pfmea' AND table_name=t AND column_name='plant_id') THEN
   FOR pol IN SELECT policyname FROM pg_policies WHERE schemaname='pfmea' AND tablename=t LOOP
    EXECUTE format('DROP POLICY %I ON pfmea.%I',pol.policyname,t);
   END LOOP;
   EXECUTE format('ALTER TABLE pfmea.%I ENABLE ROW LEVEL SECURITY',t);
   EXECUTE format('CREATE POLICY authorized_plant ON pfmea.%I USING (pfmea.authorized_plant(plant_id) OR (plant_id IS NULL AND nullif(current_setting(''app.current_user_id'',true),'''') IS NOT NULL)) WITH CHECK (pfmea.authorized_plant(plant_id))',t);
  END IF;
 END LOOP;
END $$;
-- Authentication must find a user before a plant can be selected. User access is enforced by admin/lookup API policies.
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE pfmea_headers ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_header ON pfmea_headers USING (pfmea.authorized_plant(plant_id) AND (
 current_setting('app.is_admin',true)='true' OR owner_id=nullif(current_setting('app.current_user_id',true),'')::bigint OR id IN (
 SELECT pfmea_id FROM pfmea_team_members WHERE user_id=nullif(current_setting('app.current_user_id',true),'')::bigint)))
 WITH CHECK (pfmea.authorized_plant(plant_id));
ALTER TABLE pfmea_worksheet_rows ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_worksheet ON pfmea_worksheet_rows USING (pfmea.authorized_pfmea(pfmea_id)) WITH CHECK (pfmea.authorized_pfmea(pfmea_id));
ALTER TABLE control_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_control_plan ON control_plans USING (pfmea.authorized_pfmea(pfmea_project_id)) WITH CHECK (pfmea.authorized_pfmea(pfmea_project_id));
ALTER TABLE control_plan_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_control_item ON control_plan_items USING (EXISTS (SELECT 1 FROM control_plans c WHERE c.id=control_plan_id)) WITH CHECK (EXISTS (SELECT 1 FROM control_plans c WHERE c.id=control_plan_id));
ALTER TABLE flowchart_steps ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_step ON flowchart_steps USING (EXISTS (SELECT 1 FROM flowcharts f WHERE f.id=flowchart_id)) WITH CHECK (EXISTS (SELECT 1 FROM flowcharts f WHERE f.id=flowchart_id));
