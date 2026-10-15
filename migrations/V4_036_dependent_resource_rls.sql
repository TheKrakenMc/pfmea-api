-- Definer evaluates membership without recursive team/header policies; all identifiers are qualified.
CREATE OR REPLACE FUNCTION pfmea.authorized_pfmea(p bigint) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,pfmea AS $$
 SELECT current_setting('app.is_admin',true)='true' OR EXISTS (
 SELECT 1 FROM pfmea.pfmea_headers h WHERE h.id=p AND pfmea.authorized_plant(h.plant_id) AND (
 h.owner_id=nullif(current_setting('app.current_user_id',true),'')::bigint OR EXISTS (
 SELECT 1 FROM pfmea.pfmea_team_members t WHERE t.pfmea_id=h.id AND t.user_id=nullif(current_setting('app.current_user_id',true),'')::bigint)));
$$;
ALTER TABLE pfmea.pfmea_team_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_membership ON pfmea.pfmea_team_members USING (pfmea.authorized_pfmea(pfmea_id)) WITH CHECK (pfmea.authorized_pfmea(pfmea_id));
ALTER TABLE pfmea.product_parameters ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_product_parameter ON pfmea.product_parameters USING (EXISTS(SELECT 1 FROM pfmea.products p WHERE p.id=product_id)) WITH CHECK (EXISTS(SELECT 1 FROM pfmea.products p WHERE p.id=product_id));
ALTER TABLE pfmea.product_technology_mappings ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_product_technology ON pfmea.product_technology_mappings USING (EXISTS(SELECT 1 FROM pfmea.products p WHERE p.id=product_id)) WITH CHECK (EXISTS(SELECT 1 FROM pfmea.products p WHERE p.id=product_id));
ALTER TABLE pfmea.control_plan_reactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_control_reaction ON pfmea.control_plan_reactions USING (EXISTS(SELECT 1 FROM pfmea.control_plan_items i WHERE i.id=control_plan_item_id)) WITH CHECK (EXISTS(SELECT 1 FROM pfmea.control_plan_items i WHERE i.id=control_plan_item_id));
ALTER TABLE pfmea.document_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_document_version ON pfmea.document_versions USING (
 current_setting('app.is_admin',true)='true' OR
 (document_type IN ('pfmea','pfmea_project') AND pfmea.authorized_pfmea(document_id)) OR
 (document_type='control_plan' AND EXISTS(SELECT 1 FROM pfmea.control_plans c WHERE c.id=document_id)) OR
 (document_type='flowchart' AND EXISTS(SELECT 1 FROM pfmea.flowcharts f WHERE f.id=document_id)) OR
 (document_type='product' AND EXISTS(SELECT 1 FROM pfmea.products p WHERE p.id=document_id)))
 WITH CHECK (created_by=nullif(current_setting('app.current_user_id',true),'')::bigint);
ALTER TABLE pfmea.document_audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY authorized_audit ON pfmea.document_audit_logs USING (
 current_setting('app.is_admin',true)='true' OR performed_by=nullif(current_setting('app.current_user_id',true),'')::bigint OR
 pfmea.authorized_pfmea(pfmea_project_id) OR EXISTS(SELECT 1 FROM pfmea.control_plans c WHERE c.id=control_plan_id) OR EXISTS(SELECT 1 FROM pfmea.flowcharts f WHERE f.id=flowchart_id))
 WITH CHECK (performed_by=nullif(current_setting('app.current_user_id',true),'')::bigint);
