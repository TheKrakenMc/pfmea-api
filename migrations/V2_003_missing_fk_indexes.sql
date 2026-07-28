-- ============================================================================
-- PFMEA v2 — Migration 003: Missing FK Indexes
-- ============================================================================
-- Adds indexes on every REFERENCES column that lacked an explicit index.
-- Uses CREATE INDEX IF NOT EXISTS for idempotency.
-- ============================================================================

BEGIN;

SAVEPOINT sp_fk_indexes;

-- ── plants ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_plants_region_id
    ON plants(region_id);

-- ── products ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_products_customer_id
    ON products(customer_id);

-- ── flowcharts ──────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_flowcharts_created_by
    ON flowcharts(created_by);
CREATE INDEX IF NOT EXISTS idx_flowcharts_manufacturing_location_id
    ON flowcharts(manufacturing_location_id);

-- ── flowchart_steps ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_flowchart_steps_mfg_operation_id
    ON flowchart_steps(manufacturing_operation_id);

-- ── flowchart_revisions ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_flowchart_revisions_created_by
    ON flowchart_revisions(created_by);

-- ── flowchart_approvals ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_flowchart_approvals_approved_by
    ON flowchart_approvals(approved_by);

-- ── pfmea_team_members ──────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pfmea_team_members_user_id
    ON pfmea_team_members(user_id);

-- ── process_work_elements ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_process_work_elements_step_id
    ON process_work_elements(process_step_id);

-- ── process_failure_modes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_process_failure_modes_responsible
    ON process_failure_modes(responsible_user_id);

-- ── process_parameter_controls ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_process_param_controls_responsible
    ON process_parameter_controls(responsible_user_id);

-- ── control_plan_items ──────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_cp_items_failure_mode_id
    ON control_plan_items(process_failure_mode_id);
CREATE INDEX IF NOT EXISTS idx_cp_items_param_control_id
    ON control_plan_items(process_parameter_control_id);

-- ── control_plan_reactions ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_cp_reactions_responsible
    ON control_plan_reactions(responsible_user_id);

-- ── control_plan_revisions ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_cp_revisions_created_by
    ON control_plan_revisions(created_by);

-- ── operation_instruction_sheets ────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ois_owner_id
    ON operation_instruction_sheets(owner_id);
CREATE INDEX IF NOT EXISTS idx_ois_created_by
    ON operation_instruction_sheets(created_by);

-- ── instruction_safety_measures ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_instr_safety_responsible
    ON instruction_safety_measures(responsible_user_id);

-- ── operation_instruction_revisions ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_oir_created_by
    ON operation_instruction_revisions(created_by);

-- ── document_approvals_workflow ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_daw_required_role_id
    ON document_approvals_workflow(required_role_id);
CREATE INDEX IF NOT EXISTS idx_daw_reviewer_user_id
    ON document_approvals_workflow(reviewer_user_id);
CREATE INDEX IF NOT EXISTS idx_daw_flowchart_id
    ON document_approvals_workflow(flowchart_id);
CREATE INDEX IF NOT EXISTS idx_daw_pfmea_project_id
    ON document_approvals_workflow(pfmea_project_id);
CREATE INDEX IF NOT EXISTS idx_daw_control_plan_id
    ON document_approvals_workflow(control_plan_id);
CREATE INDEX IF NOT EXISTS idx_daw_ois_id
    ON document_approvals_workflow(operation_instruction_sheet_id);

-- ── technical_documents ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tech_docs_customer_id
    ON technical_documents(customer_id);
CREATE INDEX IF NOT EXISTS idx_tech_docs_created_by
    ON technical_documents(created_by);

-- ── document_traceability ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_doc_trace_parent_flowchart_id
    ON document_traceability(parent_flowchart_id);

RELEASE SAVEPOINT sp_fk_indexes;

COMMIT;
