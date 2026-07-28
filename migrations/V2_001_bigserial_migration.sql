-- ============================================================================
-- PFMEA v2 — Migration 001: serial → bigserial (ALL PKs + FK columns)
-- ============================================================================
-- Converts every primary key from serial (int4) to bigserial (int8)
-- and every FK column that references those PKs to bigint.
-- PostgreSQL handles implicit cast int4 → int8 without data loss.
-- ============================================================================

BEGIN;

SAVEPOINT sp_bigserial;

-- ────────────────────────────────────────────────────────────────────────────
-- 1. PRIMARY KEYS  (serial → bigserial)
-- ────────────────────────────────────────────────────────────────────────────

ALTER TABLE roles                        ALTER COLUMN id TYPE bigint;
ALTER TABLE regions                      ALTER COLUMN id TYPE bigint;
ALTER TABLE plants                       ALTER COLUMN id TYPE bigint;
ALTER TABLE users                        ALTER COLUMN id TYPE bigint;
ALTER TABLE customers                    ALTER COLUMN id TYPE bigint;
ALTER TABLE products                     ALTER COLUMN id TYPE bigint;
ALTER TABLE manufacturing_locations      ALTER COLUMN id TYPE bigint;
ALTER TABLE manufacturing_operations     ALTER COLUMN id TYPE bigint;
ALTER TABLE flowcharts                   ALTER COLUMN id TYPE bigint;
ALTER TABLE flowchart_steps              ALTER COLUMN id TYPE bigint;
ALTER TABLE flowchart_revisions          ALTER COLUMN id TYPE bigint;
ALTER TABLE flowchart_approvals          ALTER COLUMN id TYPE bigint;
ALTER TABLE pfmea_projects               ALTER COLUMN id TYPE bigint;
ALTER TABLE pfmea_team_members           ALTER COLUMN id TYPE bigint;
ALTER TABLE process_items                ALTER COLUMN id TYPE bigint;
ALTER TABLE process_steps                ALTER COLUMN id TYPE bigint;
ALTER TABLE process_work_elements        ALTER COLUMN id TYPE bigint;
ALTER TABLE process_failure_modes        ALTER COLUMN id TYPE bigint;
ALTER TABLE process_parameter_controls   ALTER COLUMN id TYPE bigint;
ALTER TABLE control_plans                ALTER COLUMN id TYPE bigint;
ALTER TABLE control_plan_items           ALTER COLUMN id TYPE bigint;
ALTER TABLE control_point_characteristics ALTER COLUMN id TYPE bigint;
ALTER TABLE control_plan_reactions       ALTER COLUMN id TYPE bigint;
ALTER TABLE control_plan_revisions       ALTER COLUMN id TYPE bigint;
ALTER TABLE operation_instruction_sheets ALTER COLUMN id TYPE bigint;
ALTER TABLE instruction_steps            ALTER COLUMN id TYPE bigint;
ALTER TABLE instruction_required_materials  ALTER COLUMN id TYPE bigint;
ALTER TABLE instruction_required_equipment  ALTER COLUMN id TYPE bigint;
ALTER TABLE instruction_safety_measures     ALTER COLUMN id TYPE bigint;
ALTER TABLE instruction_quality_checks      ALTER COLUMN id TYPE bigint;
ALTER TABLE operation_instruction_revisions ALTER COLUMN id TYPE bigint;
ALTER TABLE document_audit_logs             ALTER COLUMN id TYPE bigint;
ALTER TABLE document_approvals_workflow     ALTER COLUMN id TYPE bigint;
ALTER TABLE technical_documents             ALTER COLUMN id TYPE bigint;
ALTER TABLE document_traceability           ALTER COLUMN id TYPE bigint;

-- ────────────────────────────────────────────────────────────────────────────
-- 2. FOREIGN KEY COLUMNS  (int → bigint)
-- ────────────────────────────────────────────────────────────────────────────

-- plants
ALTER TABLE plants ALTER COLUMN region_id TYPE bigint;

-- users
ALTER TABLE users ALTER COLUMN role_id   TYPE bigint;
ALTER TABLE users ALTER COLUMN plant_id  TYPE bigint;

-- customers
ALTER TABLE customers ALTER COLUMN plant_id TYPE bigint;

-- products
ALTER TABLE products ALTER COLUMN plant_id    TYPE bigint;
ALTER TABLE products ALTER COLUMN customer_id TYPE bigint;

-- manufacturing_locations
ALTER TABLE manufacturing_locations ALTER COLUMN plant_id TYPE bigint;

-- manufacturing_operations
ALTER TABLE manufacturing_operations ALTER COLUMN plant_id TYPE bigint;

-- flowcharts
ALTER TABLE flowcharts ALTER COLUMN plant_id                  TYPE bigint;
ALTER TABLE flowcharts ALTER COLUMN product_id                TYPE bigint;
ALTER TABLE flowcharts ALTER COLUMN owner_id                  TYPE bigint;
ALTER TABLE flowcharts ALTER COLUMN manufacturing_location_id TYPE bigint;
ALTER TABLE flowcharts ALTER COLUMN created_by                TYPE bigint;

-- flowchart_steps
ALTER TABLE flowchart_steps ALTER COLUMN flowchart_id              TYPE bigint;
ALTER TABLE flowchart_steps ALTER COLUMN manufacturing_operation_id TYPE bigint;

-- flowchart_revisions
ALTER TABLE flowchart_revisions ALTER COLUMN flowchart_id TYPE bigint;
ALTER TABLE flowchart_revisions ALTER COLUMN created_by   TYPE bigint;

-- flowchart_approvals
ALTER TABLE flowchart_approvals ALTER COLUMN flowchart_id TYPE bigint;
ALTER TABLE flowchart_approvals ALTER COLUMN reviewed_by  TYPE bigint;
ALTER TABLE flowchart_approvals ALTER COLUMN approved_by  TYPE bigint;

-- pfmea_projects
ALTER TABLE pfmea_projects ALTER COLUMN flowchart_id TYPE bigint;
ALTER TABLE pfmea_projects ALTER COLUMN plant_id     TYPE bigint;
ALTER TABLE pfmea_projects ALTER COLUMN owner_id     TYPE bigint;

-- pfmea_team_members
ALTER TABLE pfmea_team_members ALTER COLUMN pfmea_project_id TYPE bigint;
ALTER TABLE pfmea_team_members ALTER COLUMN user_id          TYPE bigint;

-- process_items
ALTER TABLE process_items ALTER COLUMN pfmea_project_id TYPE bigint;

-- process_steps
ALTER TABLE process_steps ALTER COLUMN process_item_id TYPE bigint;

-- process_work_elements
ALTER TABLE process_work_elements ALTER COLUMN process_step_id TYPE bigint;

-- process_failure_modes
ALTER TABLE process_failure_modes ALTER COLUMN process_step_id     TYPE bigint;
ALTER TABLE process_failure_modes ALTER COLUMN responsible_user_id TYPE bigint;

-- process_parameter_controls
ALTER TABLE process_parameter_controls ALTER COLUMN process_step_id     TYPE bigint;
ALTER TABLE process_parameter_controls ALTER COLUMN responsible_user_id TYPE bigint;

-- control_plans
ALTER TABLE control_plans ALTER COLUMN pfmea_project_id TYPE bigint;
ALTER TABLE control_plans ALTER COLUMN flowchart_id     TYPE bigint;
ALTER TABLE control_plans ALTER COLUMN owner_id         TYPE bigint;
ALTER TABLE control_plans ALTER COLUMN created_by       TYPE bigint;

-- control_plan_items
ALTER TABLE control_plan_items ALTER COLUMN control_plan_id              TYPE bigint;
ALTER TABLE control_plan_items ALTER COLUMN process_failure_mode_id      TYPE bigint;
ALTER TABLE control_plan_items ALTER COLUMN process_parameter_control_id TYPE bigint;

-- control_point_characteristics
ALTER TABLE control_point_characteristics ALTER COLUMN control_plan_item_id TYPE bigint;

-- control_plan_reactions
ALTER TABLE control_plan_reactions ALTER COLUMN control_plan_item_id  TYPE bigint;
ALTER TABLE control_plan_reactions ALTER COLUMN responsible_user_id   TYPE bigint;

-- control_plan_revisions
ALTER TABLE control_plan_revisions ALTER COLUMN control_plan_id TYPE bigint;
ALTER TABLE control_plan_revisions ALTER COLUMN created_by      TYPE bigint;

-- operation_instruction_sheets
ALTER TABLE operation_instruction_sheets ALTER COLUMN control_plan_id  TYPE bigint;
ALTER TABLE operation_instruction_sheets ALTER COLUMN flowchart_id     TYPE bigint;
ALTER TABLE operation_instruction_sheets ALTER COLUMN process_step_id  TYPE bigint;
ALTER TABLE operation_instruction_sheets ALTER COLUMN owner_id         TYPE bigint;
ALTER TABLE operation_instruction_sheets ALTER COLUMN created_by       TYPE bigint;

-- instruction_steps
ALTER TABLE instruction_steps ALTER COLUMN operation_instruction_sheet_id TYPE bigint;

-- instruction_required_materials
ALTER TABLE instruction_required_materials ALTER COLUMN operation_instruction_sheet_id TYPE bigint;

-- instruction_required_equipment
ALTER TABLE instruction_required_equipment ALTER COLUMN operation_instruction_sheet_id TYPE bigint;

-- instruction_safety_measures
ALTER TABLE instruction_safety_measures ALTER COLUMN operation_instruction_sheet_id TYPE bigint;
ALTER TABLE instruction_safety_measures ALTER COLUMN responsible_user_id            TYPE bigint;

-- instruction_quality_checks
ALTER TABLE instruction_quality_checks ALTER COLUMN operation_instruction_sheet_id TYPE bigint;

-- operation_instruction_revisions
ALTER TABLE operation_instruction_revisions ALTER COLUMN operation_instruction_sheet_id TYPE bigint;
ALTER TABLE operation_instruction_revisions ALTER COLUMN created_by                    TYPE bigint;

-- document_audit_logs
ALTER TABLE document_audit_logs ALTER COLUMN flowchart_id                    TYPE bigint;
ALTER TABLE document_audit_logs ALTER COLUMN pfmea_project_id                TYPE bigint;
ALTER TABLE document_audit_logs ALTER COLUMN control_plan_id                 TYPE bigint;
ALTER TABLE document_audit_logs ALTER COLUMN operation_instruction_sheet_id  TYPE bigint;
ALTER TABLE document_audit_logs ALTER COLUMN performed_by                    TYPE bigint;

-- document_approvals_workflow
ALTER TABLE document_approvals_workflow ALTER COLUMN document_id                    TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN flowchart_id                   TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN pfmea_project_id               TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN control_plan_id                TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN operation_instruction_sheet_id  TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN required_role_id               TYPE bigint;
ALTER TABLE document_approvals_workflow ALTER COLUMN reviewer_user_id               TYPE bigint;

-- technical_documents
ALTER TABLE technical_documents ALTER COLUMN plant_id                        TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN customer_id                     TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN flowchart_id                    TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN pfmea_project_id                TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN control_plan_id                 TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN operation_instruction_sheet_id  TYPE bigint;
ALTER TABLE technical_documents ALTER COLUMN created_by                      TYPE bigint;

-- document_traceability
ALTER TABLE document_traceability ALTER COLUMN parent_document_id  TYPE bigint;
ALTER TABLE document_traceability ALTER COLUMN child_document_id   TYPE bigint;
ALTER TABLE document_traceability ALTER COLUMN flowchart_id        TYPE bigint;
ALTER TABLE document_traceability ALTER COLUMN parent_flowchart_id TYPE bigint;

RELEASE SAVEPOINT sp_bigserial;

COMMIT;
