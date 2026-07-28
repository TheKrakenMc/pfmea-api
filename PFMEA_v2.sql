CREATE TABLE "roles" (
  "id" serial PRIMARY KEY,
  "name" varchar UNIQUE NOT NULL,
  "description" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "regions" (
  "id" serial PRIMARY KEY,
  "name" varchar UNIQUE NOT NULL,
  "code" varchar UNIQUE NOT NULL,
  "description" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "plants" (
  "id" serial PRIMARY KEY,
  "region_id" int NOT NULL,
  "name" varchar NOT NULL,
  "code" varchar UNIQUE NOT NULL,
  "address" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now())
);

CREATE TABLE "users" (
  "id" serial PRIMARY KEY,
  "role_id" int NOT NULL,
  "plant_id" int NOT NULL,
  "full_name" varchar NOT NULL,
  "email" varchar UNIQUE NOT NULL,
  "employment_position" varchar,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now())
);

CREATE TABLE "customers" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "customer_code" varchar UNIQUE NOT NULL,
  "company_name" varchar NOT NULL,
  "tax_registry" varchar,
  "status" varchar DEFAULT 'active',
  "address" text,
  "city" varchar,
  "state" varchar,
  "postal_code" varchar,
  "country" varchar,
  "contact_email" varchar,
  "logo_url" varchar,
  "brand_logo_url" varchar,
  "provider_code" varchar,
  "observations" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now())
);

CREATE TABLE "products" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "customer_id" int,
  "part_number" varchar NOT NULL,
  "customer_part_number" varchar,
  "description" text,
  "status" varchar DEFAULT 'active',
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now())
);

CREATE TABLE "manufacturing_locations" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "location_code" varchar NOT NULL,
  "location_name" varchar NOT NULL,
  "location_type" varchar,
  "description" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "manufacturing_operations" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "operation_name" varchar NOT NULL,
  "operation_code" varchar UNIQUE,
  "description" text,
  "operation_type" varchar,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "flowcharts" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "product_id" int NOT NULL,
  "owner_id" int NOT NULL,
  "flowchart_code" varchar UNIQUE NOT NULL,
  "title" varchar NOT NULL,
  "version" int DEFAULT 1,
  "status" varchar DEFAULT 'Draft',
  "production_stage" varchar,
  "manufacturing_location_id" int,
  "description" text,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now()),
  "observations" text,
  "is_active" boolean DEFAULT true
);

CREATE TABLE "flowchart_steps" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int NOT NULL,
  "manufacturing_operation_id" int,
  "step_number" int NOT NULL,
  "step_sequence" int NOT NULL,
  "step_name" varchar,
  "custom_description" varchar
);

CREATE TABLE "flowchart_revisions" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int NOT NULL,
  "revision_number" int NOT NULL,
  "change_reason" varchar NOT NULL,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "original_creation_date" timestamptz NOT NULL,
  "observations" text,
  "is_initial_revision" boolean DEFAULT false
);

CREATE TABLE "flowchart_approvals" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int NOT NULL,
  "reviewed_by" int NOT NULL,
  "approved_by" int,
  "review_status" varchar DEFAULT 'pending',
  "reviewed_at" timestamptz,
  "approved_at" timestamptz,
  "review_comments" text
);

CREATE TABLE "pfmea_projects" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int NOT NULL,
  "plant_id" int NOT NULL,
  "pfmea_code" varchar UNIQUE NOT NULL,
  "title" varchar NOT NULL,
  "owner_id" int NOT NULL,
  "status" varchar DEFAULT 'Draft',
  "confidentiality_level" varchar DEFAULT 'Internal',
  "start_date" date NOT NULL,
  "last_revision_date" date,
  "version" int DEFAULT 1,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now())
);

CREATE TABLE "pfmea_team_members" (
  "id" serial PRIMARY KEY,
  "pfmea_project_id" int NOT NULL,
  "user_id" int NOT NULL,
  "role_in_team" varchar,
  "assigned_at" timestamptz DEFAULT (now())
);

CREATE TABLE "process_items" (
  "id" serial PRIMARY KEY,
  "pfmea_project_id" int NOT NULL,
  "item_name" varchar NOT NULL,
  "item_type" varchar,
  "description" text,
  "sequence_order" int NOT NULL
);

CREATE TABLE "process_steps" (
  "id" serial PRIMARY KEY,
  "process_item_id" int NOT NULL,
  "station_number" varchar,
  "step_name" varchar NOT NULL,
  "sequence_order" int NOT NULL,
  "description" text
);

CREATE TABLE "process_work_elements" (
  "id" serial PRIMARY KEY,
  "process_step_id" int NOT NULL,
  "element_type" varchar NOT NULL,
  "element_name" varchar,
  "description" text,
  "specific_instructions" text
);

CREATE TABLE "process_failure_modes" (
  "id" serial PRIMARY KEY,
  "process_step_id" int NOT NULL,
  "failure_mode_description" varchar NOT NULL,
  "failure_effects" text,
  "failure_causes" text,
  "severity" int,
  "occurrence" int,
  "detection" int,
  "rpn" int,
  "recommended_action" text,
  "responsible_user_id" int,
  "action_deadline" date
);

CREATE TABLE "process_parameter_controls" (
  "id" serial PRIMARY KEY,
  "process_step_id" int NOT NULL,
  "parameter_name" varchar NOT NULL,
  "unit_of_measure" varchar,
  "lower_spec_limit" numeric,
  "upper_spec_limit" numeric,
  "target_value" numeric,
  "nominal_value" numeric,
  "monitoring_method" varchar,
  "measurement_frequency" varchar,
  "responsible_user_id" int
);

CREATE TABLE "control_plans" (
  "id" serial PRIMARY KEY,
  "pfmea_project_id" int NOT NULL,
  "flowchart_id" int NOT NULL,
  "control_plan_code" varchar UNIQUE NOT NULL,
  "title" varchar NOT NULL,
  "owner_id" int NOT NULL,
  "status" varchar DEFAULT 'Draft',
  "version" int DEFAULT 1,
  "start_date" date NOT NULL,
  "last_revision_date" date,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now()),
  "observations" text,
  "is_active" boolean DEFAULT true
);

CREATE TABLE "control_plan_items" (
  "id" serial PRIMARY KEY,
  "control_plan_id" int NOT NULL,
  "process_failure_mode_id" int,
  "process_parameter_control_id" int,
  "item_sequence" int NOT NULL,
  "item_name" varchar NOT NULL
);

CREATE TABLE "control_point_characteristics" (
  "id" serial PRIMARY KEY,
  "control_plan_item_id" int NOT NULL,
  "characteristic_name" varchar NOT NULL,
  "characteristic_type" varchar,
  "lower_tolerance" numeric,
  "upper_tolerance" numeric,
  "measurement_method" varchar,
  "sampling_plan" varchar,
  "acceptance_criteria" varchar,
  "rejection_criteria" varchar
);

CREATE TABLE "control_plan_reactions" (
  "id" serial PRIMARY KEY,
  "control_plan_item_id" int NOT NULL,
  "reaction_type" varchar,
  "reaction_description" text,
  "responsible_user_id" int
);

CREATE TABLE "control_plan_revisions" (
  "id" serial PRIMARY KEY,
  "control_plan_id" int NOT NULL,
  "revision_number" int NOT NULL,
  "change_reason" varchar NOT NULL,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "original_creation_date" timestamptz NOT NULL,
  "observations" text
);

CREATE TABLE "operation_instruction_sheets" (
  "id" serial PRIMARY KEY,
  "control_plan_id" int NOT NULL,
  "flowchart_id" int NOT NULL,
  "instruction_code" varchar UNIQUE NOT NULL,
  "title" varchar NOT NULL,
  "process_step_id" int,
  "owner_id" int NOT NULL,
  "status" varchar DEFAULT 'Draft',
  "version" int DEFAULT 1,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "updated_at" timestamptz DEFAULT (now()),
  "is_active" boolean DEFAULT true
);

CREATE TABLE "instruction_steps" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "step_sequence" int NOT NULL,
  "step_title" varchar NOT NULL,
  "step_description" text NOT NULL,
  "warning_message" text,
  "image_reference" varchar,
  "estimated_time_seconds" int
);

CREATE TABLE "instruction_required_materials" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "material_name" varchar NOT NULL,
  "material_specification" varchar,
  "quantity" numeric,
  "unit_of_measure" varchar,
  "notes" text
);

CREATE TABLE "instruction_required_equipment" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "equipment_name" varchar NOT NULL,
  "equipment_code" varchar,
  "specification" varchar,
  "quantity" int,
  "notes" text
);

CREATE TABLE "instruction_safety_measures" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "safety_measure_description" text NOT NULL,
  "hazard_level" varchar,
  "required_ppe" varchar,
  "responsible_user_id" int
);

CREATE TABLE "instruction_quality_checks" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "check_sequence" int NOT NULL,
  "check_description" text NOT NULL,
  "acceptance_criteria" text NOT NULL,
  "checkpoint_location" varchar
);

CREATE TABLE "operation_instruction_revisions" (
  "id" serial PRIMARY KEY,
  "operation_instruction_sheet_id" int NOT NULL,
  "revision_number" int NOT NULL,
  "change_reason" varchar NOT NULL,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "original_creation_date" timestamptz NOT NULL,
  "observations" text
);

CREATE TABLE "document_audit_logs" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int,
  "pfmea_project_id" int,
  "control_plan_id" int,
  "operation_instruction_sheet_id" int,
  "action" varchar NOT NULL,
  "performed_by" int NOT NULL,
  "action_details" text,
  "previous_values" jsonb,
  "new_values" jsonb,
  "performed_at" timestamptz DEFAULT (now())
);

CREATE TABLE "document_approvals_workflow" (
  "id" serial PRIMARY KEY,
  "document_type" varchar NOT NULL,
  "document_id" int NOT NULL,
  "flowchart_id" int,
  "pfmea_project_id" int,
  "control_plan_id" int,
  "operation_instruction_sheet_id" int,
  "approval_sequence" int NOT NULL,
  "required_role_id" int NOT NULL,
  "reviewer_user_id" int,
  "approval_status" varchar DEFAULT 'pending',
  "approved_at" timestamptz,
  "rejection_reason" text,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "technical_documents" (
  "id" serial PRIMARY KEY,
  "plant_id" int NOT NULL,
  "customer_id" int,
  "flowchart_id" int,
  "pfmea_project_id" int,
  "control_plan_id" int,
  "operation_instruction_sheet_id" int,
  "document_code" varchar UNIQUE NOT NULL,
  "document_title" varchar NOT NULL,
  "document_type" varchar,
  "status" varchar DEFAULT 'Draft',
  "document_hierarchy_level" varchar,
  "created_by" int NOT NULL,
  "created_at" timestamptz DEFAULT (now()),
  "observations" text,
  "is_active" boolean DEFAULT true
);

CREATE TABLE "document_traceability" (
  "id" serial PRIMARY KEY,
  "parent_document_type" varchar NOT NULL,
  "parent_document_id" int NOT NULL,
  "child_document_type" varchar NOT NULL,
  "child_document_id" int NOT NULL,
  "flowchart_id" int,
  "parent_flowchart_id" int,
  "relationship_type" varchar,
  "created_at" timestamptz DEFAULT (now())
);

CREATE UNIQUE INDEX ON "plants" ("region_id", "code");

CREATE INDEX ON "users" ("email");

CREATE INDEX ON "users" ("plant_id");

CREATE INDEX ON "users" ("role_id");

CREATE UNIQUE INDEX ON "customers" ("plant_id", "customer_code");

CREATE INDEX ON "customers" ("customer_code");

CREATE INDEX ON "customers" ("status");

CREATE UNIQUE INDEX ON "products" ("plant_id", "part_number");

CREATE INDEX ON "products" ("part_number");

CREATE UNIQUE INDEX ON "manufacturing_locations" ("plant_id", "location_code");

CREATE UNIQUE INDEX ON "manufacturing_operations" ("plant_id", "operation_name");

CREATE UNIQUE INDEX ON "flowcharts" ("plant_id", "flowchart_code");

CREATE INDEX ON "flowcharts" ("product_id");

CREATE INDEX ON "flowcharts" ("owner_id");

CREATE INDEX ON "flowcharts" ("status");

CREATE UNIQUE INDEX ON "flowchart_steps" ("flowchart_id", "step_number");

CREATE INDEX ON "flowchart_steps" ("flowchart_id", "step_sequence");

CREATE UNIQUE INDEX ON "flowchart_revisions" ("flowchart_id", "revision_number");

CREATE INDEX ON "flowchart_revisions" ("flowchart_id");

CREATE UNIQUE INDEX ON "flowchart_approvals" ("flowchart_id", "reviewed_by");

CREATE UNIQUE INDEX ON "pfmea_projects" ("plant_id", "pfmea_code");

CREATE INDEX ON "pfmea_projects" ("flowchart_id");

CREATE INDEX ON "pfmea_projects" ("status");

CREATE INDEX ON "pfmea_projects" ("owner_id");

CREATE UNIQUE INDEX ON "pfmea_team_members" ("pfmea_project_id", "user_id");

CREATE UNIQUE INDEX ON "process_items" ("pfmea_project_id", "sequence_order");

CREATE UNIQUE INDEX ON "process_steps" ("process_item_id", "sequence_order");

CREATE INDEX ON "process_failure_modes" ("process_step_id");

CREATE INDEX ON "process_failure_modes" ("rpn");

CREATE INDEX ON "process_parameter_controls" ("process_step_id");

CREATE UNIQUE INDEX ON "control_plans" ("flowchart_id", "control_plan_code");

CREATE INDEX ON "control_plans" ("pfmea_project_id");

CREATE INDEX ON "control_plans" ("status");

CREATE INDEX ON "control_plans" ("owner_id");

CREATE UNIQUE INDEX ON "control_plan_items" ("control_plan_id", "item_sequence");

CREATE INDEX ON "control_point_characteristics" ("control_plan_item_id");

CREATE INDEX ON "control_plan_reactions" ("control_plan_item_id");

CREATE UNIQUE INDEX ON "control_plan_revisions" ("control_plan_id", "revision_number");

CREATE UNIQUE INDEX ON "operation_instruction_sheets" ("flowchart_id", "instruction_code");

CREATE INDEX ON "operation_instruction_sheets" ("control_plan_id");

CREATE INDEX ON "operation_instruction_sheets" ("process_step_id");

CREATE INDEX ON "operation_instruction_sheets" ("status");

CREATE UNIQUE INDEX ON "instruction_steps" ("operation_instruction_sheet_id", "step_sequence");

CREATE INDEX ON "instruction_required_materials" ("operation_instruction_sheet_id");

CREATE INDEX ON "instruction_required_equipment" ("operation_instruction_sheet_id");

CREATE INDEX ON "instruction_safety_measures" ("operation_instruction_sheet_id");

CREATE UNIQUE INDEX ON "instruction_quality_checks" ("operation_instruction_sheet_id", "check_sequence");

CREATE UNIQUE INDEX ON "operation_instruction_revisions" ("operation_instruction_sheet_id", "revision_number");

CREATE INDEX ON "document_audit_logs" ("flowchart_id", "performed_at");

CREATE INDEX ON "document_audit_logs" ("pfmea_project_id", "performed_at");

CREATE INDEX ON "document_audit_logs" ("control_plan_id", "performed_at");

CREATE INDEX ON "document_audit_logs" ("operation_instruction_sheet_id", "performed_at");

CREATE INDEX ON "document_audit_logs" ("performed_by");

CREATE INDEX ON "document_audit_logs" ("performed_at");

CREATE UNIQUE INDEX ON "document_approvals_workflow" ("document_type", "document_id", "approval_sequence");

CREATE INDEX ON "document_approvals_workflow" ("approval_status");

CREATE UNIQUE INDEX ON "technical_documents" ("plant_id", "document_code");

CREATE INDEX ON "technical_documents" ("flowchart_id");

CREATE INDEX ON "technical_documents" ("pfmea_project_id");

CREATE INDEX ON "technical_documents" ("control_plan_id");

CREATE INDEX ON "technical_documents" ("operation_instruction_sheet_id");

CREATE INDEX ON "technical_documents" ("status");

CREATE INDEX ON "document_traceability" ("parent_document_type", "parent_document_id");

CREATE INDEX ON "document_traceability" ("child_document_type", "child_document_id");

CREATE INDEX ON "document_traceability" ("flowchart_id");

COMMENT ON TABLE "roles" IS 'Administrator, PFMEA Owner, Team Member, Viewer, Process Engineer';

COMMENT ON TABLE "regions" IS 'NAFTA, EMEA, APAC, etc.';

ALTER TABLE "plants" ADD FOREIGN KEY ("region_id") REFERENCES "regions" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "users" ADD FOREIGN KEY ("role_id") REFERENCES "roles" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "users" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "customers" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "products" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "products" ADD FOREIGN KEY ("customer_id") REFERENCES "customers" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "manufacturing_locations" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "manufacturing_operations" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("product_id") REFERENCES "products" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("manufacturing_location_id") REFERENCES "manufacturing_locations" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_steps" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_steps" ADD FOREIGN KEY ("manufacturing_operation_id") REFERENCES "manufacturing_operations" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_revisions" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_revisions" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_approvals" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_approvals" ADD FOREIGN KEY ("reviewed_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_approvals" ADD FOREIGN KEY ("approved_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_projects" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_projects" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_projects" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_team_members" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_team_members" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_items" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_steps" ADD FOREIGN KEY ("process_item_id") REFERENCES "process_items" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_work_elements" ADD FOREIGN KEY ("process_step_id") REFERENCES "process_steps" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_failure_modes" ADD FOREIGN KEY ("process_step_id") REFERENCES "process_steps" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_failure_modes" ADD FOREIGN KEY ("responsible_user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_parameter_controls" ADD FOREIGN KEY ("process_step_id") REFERENCES "process_steps" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_parameter_controls" ADD FOREIGN KEY ("responsible_user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plans" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plans" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plans" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plans" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_items" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_items" ADD FOREIGN KEY ("process_failure_mode_id") REFERENCES "process_failure_modes" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_items" ADD FOREIGN KEY ("process_parameter_control_id") REFERENCES "process_parameter_controls" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_point_characteristics" ADD FOREIGN KEY ("control_plan_item_id") REFERENCES "control_plan_items" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_reactions" ADD FOREIGN KEY ("control_plan_item_id") REFERENCES "control_plan_items" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_reactions" ADD FOREIGN KEY ("responsible_user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_revisions" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "control_plan_revisions" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_sheets" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_sheets" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_sheets" ADD FOREIGN KEY ("process_step_id") REFERENCES "process_steps" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_sheets" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_sheets" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_steps" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_required_materials" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_required_equipment" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_safety_measures" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_safety_measures" ADD FOREIGN KEY ("responsible_user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "instruction_quality_checks" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_revisions" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "operation_instruction_revisions" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_audit_logs" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_audit_logs" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_audit_logs" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_audit_logs" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_audit_logs" ADD FOREIGN KEY ("performed_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("required_role_id") REFERENCES "roles" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_approvals_workflow" ADD FOREIGN KEY ("reviewer_user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("customer_id") REFERENCES "customers" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("pfmea_project_id") REFERENCES "pfmea_projects" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("control_plan_id") REFERENCES "control_plans" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("operation_instruction_sheet_id") REFERENCES "operation_instruction_sheets" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technical_documents" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_traceability" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "document_traceability" ADD FOREIGN KEY ("parent_flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;
