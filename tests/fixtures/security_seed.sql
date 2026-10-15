
 INSERT INTO regions(id,name,code) VALUES(1,'Test Region','TEST');
 INSERT INTO plants(id,region_id,name,code) VALUES(1,1,'Plant One','ONE'),(2,1,'Plant Two','TWO');
 INSERT INTO roles(id,name) VALUES(1,'PFMEA Owner'),(2,'Administrator');
 INSERT INTO users(id,role_id,plant_id,email,full_name,is_verified,must_change_password) VALUES(1,1,1,'owner@example.com','Owner',true,false),(2,1,2,'other@example.com','Other',true,false);
 INSERT INTO customers(id,plant_id,customer_code,company_name) VALUES(1,1,'C1','Customer One'),(2,2,'C2','Customer Two');
 INSERT INTO products(id,plant_id,customer_id,part_number) VALUES(1,1,1,'PART-1'),(2,2,2,'PART-2');
 INSERT INTO flowcharts(id,plant_id,product_id,owner_id,created_by,title,status) VALUES(1,1,1,1,1,'Flow One','Approved'),(2,2,2,2,2,'Flow Two','Approved');
 INSERT INTO pfmea_headers(id,flowchart_id,plant_id,owner_id,pfmea_id_number,project_name,moc_status,status) VALUES(1,1,1,1,'PFMEA-1','Project One','Approved','Approved'),(2,2,2,2,'PFMEA-2','Project Two','Approved','Approved');
 INSERT INTO pfmea_team_members(pfmea_id,user_id,role_in_team,department) VALUES(1,1,'PFMEA Owner','Quality'),(2,2,'PFMEA Owner','Quality');
 INSERT INTO pfmea_worksheet_rows(id,pfmea_id,station_operation,failure_mode,severity,occurrence,detection,action_priority) VALUES(1,1,'Step','Failure',9,1,7,'H'),(2,2,'Step','Failure',9,1,7,'H');
 INSERT INTO control_plans(id,pfmea_project_id,flowchart_id,control_plan_code,title,owner_id,created_by,start_date) VALUES(1,1,1,'CP-1','Plan One',1,1,current_date),(2,2,2,'CP-2','Plan Two',2,2,current_date);
 INSERT INTO control_plan_items(id,control_plan_id,item_sequence,item_name) VALUES(1,1,10,'Mode: Failure (Step: Step)'),(2,2,10,'Mode: Failure (Step: Step)');
