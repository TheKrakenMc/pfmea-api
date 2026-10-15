
CREATE TABLE measurement_units (
	id BIGSERIAL NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	symbology VARCHAR(50) NOT NULL, 
	magnitude VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE plants (
	id BIGSERIAL NOT NULL, 
	region_id BIGINT, 
	name VARCHAR, 
	code VARCHAR, 
	address VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

CREATE TABLE regions (
	id BIGSERIAL NOT NULL, 
	name VARCHAR, 
	code VARCHAR, 
	description VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
)

;

CREATE TABLE roles (
	id BIGSERIAL NOT NULL, 
	name VARCHAR, 
	description VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

CREATE TABLE technology_categories (
	id SERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	description VARCHAR, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_technology_categories_name UNIQUE (name)
)

;
CREATE UNIQUE INDEX ix_technology_categories_name ON technology_categories (name);
COMMENT ON COLUMN technology_categories.name IS 'Category Name';

CREATE TABLE users (
	id BIGSERIAL NOT NULL, 
	role_id BIGINT, 
	plant_id BIGINT, 
	full_name VARCHAR, 
	email VARCHAR, 
	password_hash VARCHAR, 
	employment_position VARCHAR, 
	department_id BIGINT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	is_verified BOOLEAN DEFAULT 'false' NOT NULL, 
	must_change_password BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;
COMMENT ON COLUMN users.plant_id IS 'Primary location of the user';

CREATE TABLE product_families (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	description TEXT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE UNIQUE INDEX ix_product_families_name ON product_families (name);

CREATE TABLE production_lines (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	description TEXT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE UNIQUE INDEX ix_production_lines_name ON production_lines (name);

CREATE TABLE departments (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

CREATE TABLE customers (
	id BIGSERIAL NOT NULL, 
	plant_id BIGINT NOT NULL, 
	customer_code VARCHAR NOT NULL, 
	company_name VARCHAR NOT NULL, 
	tax_registry VARCHAR, 
	status VARCHAR DEFAULT '''active''', 
	address VARCHAR, 
	city VARCHAR, 
	state VARCHAR, 
	postal_code VARCHAR, 
	country VARCHAR, 
	contact_email VARCHAR, 
	logo_url VARCHAR, 
	brand_logo_url VARCHAR, 
	provider_code VARCHAR, 
	observations VARCHAR, 
	safety_characteristic VARCHAR DEFAULT '''D''', 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	UNIQUE (customer_code), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;
CREATE INDEX ix_customers_customer_code ON customers (customer_code);
CREATE INDEX ix_customers_status ON customers (status);

CREATE TABLE document_approvals (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE document_traceabilities (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE document_versions (
	id BIGSERIAL NOT NULL, 
	document_type VARCHAR NOT NULL, 
	document_id BIGINT NOT NULL, 
	revision_number INTEGER NOT NULL, 
	change_reason VARCHAR NOT NULL, 
	created_by BIGINT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	original_creation_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	observations VARCHAR, 
	snapshot_data JSONB, 
	is_initial_revision BOOLEAN DEFAULT 'false' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;
CREATE INDEX ix_doc_versions_created_at ON document_versions (created_at);
CREATE INDEX ix_doc_versions_created_by ON document_versions (created_by);
CREATE INDEX ix_doc_versions_type_id ON document_versions (document_type, document_id);

CREATE TABLE instruction_equipments (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE instruction_materials (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE instruction_quality_checks (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE instruction_safeties (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE instruction_sheets (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE instruction_steps (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE manufacturing_locations (
	id BIGSERIAL NOT NULL, 
	plant_id BIGINT NOT NULL, 
	location_code VARCHAR NOT NULL, 
	location_name VARCHAR NOT NULL, 
	location_type VARCHAR, 
	description VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE manufacturing_operations (
	id BIGSERIAL NOT NULL, 
	plant_id BIGINT NOT NULL, 
	operation_name VARCHAR NOT NULL, 
	operation_code VARCHAR, 
	description VARCHAR, 
	operation_type VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	UNIQUE (operation_code), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE process_failure_modes (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE process_parameter_controls (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE technical_documents (
	id BIGSERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE technologies (
	id SERIAL NOT NULL, 
	code VARCHAR, 
	name VARCHAR NOT NULL, 
	category VARCHAR, 
	description VARCHAR, 
	is_active BOOLEAN NOT NULL, 
	suggested_parameters JSON, 
	created_by BIGINT, 
	updated_by BIGINT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_technologies_code UNIQUE (code), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
)

;
CREATE UNIQUE INDEX ix_technologies_code ON technologies (code);
COMMENT ON COLUMN technologies.code IS 'Technology Code (e.g. ASM-01)';
COMMENT ON COLUMN technologies.name IS 'Technology Name';
COMMENT ON COLUMN technologies.category IS 'Type/Category';

CREATE TABLE user_otps (
	id BIGSERIAL NOT NULL, 
	user_id BIGINT NOT NULL, 
	otp_code VARCHAR NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	is_used BOOLEAN DEFAULT 'false' NOT NULL, 
	attempts INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE TABLE auth_sessions (
	id VARCHAR(64) NOT NULL, 
	user_id BIGINT NOT NULL, 
	refresh_hash VARCHAR(64) NOT NULL, 
	csrf_token VARCHAR(128) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE user_plants (
	user_id BIGINT NOT NULL, 
	plant_id BIGINT NOT NULL, 
	PRIMARY KEY (user_id, plant_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id)
)

;

CREATE TABLE used_verification_tokens (
	token_hash VARCHAR(64) NOT NULL, 
	user_id BIGINT NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE products (
	lock_version INTEGER DEFAULT '1' NOT NULL, 
	needs_review BOOLEAN DEFAULT 'false' NOT NULL, 
	id BIGSERIAL NOT NULL, 
	plant_id BIGINT, 
	customer_id BIGINT, 
	product_family_id BIGINT, 
	production_line_id BIGINT, 
	part_number VARCHAR, 
	customer_part_number VARCHAR, 
	description VARCHAR, 
	engineering_level VARCHAR, 
	drawing VARCHAR, 
	stage VARCHAR, 
	dimensions VARCHAR, 
	weight FLOAT, 
	cycle_time FLOAT, 
	rate_per_hour FLOAT, 
	image_url VARCHAR, 
	status VARCHAR, 
	version INTEGER DEFAULT '1' NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(product_family_id) REFERENCES product_families (id), 
	FOREIGN KEY(production_line_id) REFERENCES production_lines (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE plant_technologies (
	plant_id INTEGER NOT NULL, 
	technology_id INTEGER NOT NULL, 
	PRIMARY KEY (plant_id, technology_id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id) ON DELETE CASCADE, 
	FOREIGN KEY(technology_id) REFERENCES technologies (id) ON DELETE CASCADE
)

;

CREATE TABLE machinery (
	id BIGSERIAL NOT NULL, 
	machinery_name VARCHAR NOT NULL, 
	machinery_code VARCHAR NOT NULL, 
	plant_id BIGINT NOT NULL, 
	location_id BIGINT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	FOREIGN KEY(location_id) REFERENCES manufacturing_locations (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE technology_parameters (
	id BIGSERIAL NOT NULL, 
	technology_id BIGINT NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	measurement_unit_id BIGINT, 
	target_value FLOAT, 
	min_value FLOAT, 
	max_value FLOAT, 
	is_critical BOOLEAN DEFAULT 'false' NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(technology_id) REFERENCES technologies (id) ON DELETE CASCADE, 
	FOREIGN KEY(measurement_unit_id) REFERENCES measurement_units (id) ON DELETE SET NULL
)

;
CREATE INDEX ix_technology_parameters_technology_id ON technology_parameters (technology_id);
COMMENT ON COLUMN technology_parameters.name IS 'Parameter name, e.g. Temperatura';
COMMENT ON COLUMN technology_parameters.target_value IS 'Nominal / target value';
COMMENT ON COLUMN technology_parameters.min_value IS 'Lower specification limit';
COMMENT ON COLUMN technology_parameters.max_value IS 'Upper specification limit';
COMMENT ON COLUMN technology_parameters.is_critical IS 'CC / SC flag';

CREATE TABLE flowcharts (
	id BIGSERIAL NOT NULL, 
	plant_id BIGINT, 
	product_id BIGINT, 
	owner_id BIGINT, 
	flowchart_code VARCHAR, 
	title VARCHAR, 
	lock_version INTEGER DEFAULT '1' NOT NULL, 
	needs_review BOOLEAN DEFAULT 'false' NOT NULL, 
	version INTEGER DEFAULT '1' NOT NULL, 
	status VARCHAR, 
	production_stage VARCHAR, 
	manufacturing_location_id BIGINT, 
	description VARCHAR, 
	created_by BIGINT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	observations VARCHAR, 
	confidentiality_level VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	UNIQUE (flowchart_code), 
	FOREIGN KEY(manufacturing_location_id) REFERENCES manufacturing_locations (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;
CREATE INDEX ix_flowcharts_product_id ON flowcharts (product_id);
COMMENT ON COLUMN flowcharts.status IS 'Draft, Approved, Archived';

CREATE TABLE product_technology_mappings (
	id BIGSERIAL NOT NULL, 
	product_id BIGINT NOT NULL, 
	technology_id BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_product_technology UNIQUE (product_id, technology_id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(technology_id) REFERENCES technologies (id) ON DELETE CASCADE
)

;

CREATE TABLE product_parameters (
	id BIGSERIAL NOT NULL, 
	product_id BIGINT NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	measurement_unit_id BIGINT, 
	technology_id BIGINT, 
	target_value FLOAT, 
	min_value FLOAT, 
	max_value FLOAT, 
	is_critical BOOLEAN DEFAULT 'false' NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	order_index INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(measurement_unit_id) REFERENCES measurement_units (id) ON DELETE SET NULL, 
	FOREIGN KEY(technology_id) REFERENCES technologies (id) ON DELETE SET NULL
)

;
CREATE INDEX ix_product_parameters_technology_id ON product_parameters (technology_id);
CREATE INDEX ix_product_parameters_product_id ON product_parameters (product_id);
COMMENT ON COLUMN product_parameters.name IS 'Parameter name, e.g. Temperatura';
COMMENT ON COLUMN product_parameters.target_value IS 'Nominal / target value';
COMMENT ON COLUMN product_parameters.min_value IS 'Lower specification limit';
COMMENT ON COLUMN product_parameters.max_value IS 'Upper specification limit';
COMMENT ON COLUMN product_parameters.is_critical IS 'CC / SC flag';

CREATE TABLE flowchart_steps (
	id SERIAL NOT NULL, 
	flowchart_id BIGINT, 
	technology_id INTEGER, 
	machinery_id BIGINT, 
	step_number INTEGER, 
	sub_step INTEGER DEFAULT '0' NOT NULL, 
	symbol_type VARCHAR DEFAULT 'operation' NOT NULL, 
	responsible_department VARCHAR NOT NULL, 
	custom_description VARCHAR, 
	critical_flag VARCHAR DEFAULT 'none' NOT NULL, 
	product_characteristics VARCHAR, 
	process_characteristics VARCHAR, 
	target VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_flowchart_steps_fc_step_sub UNIQUE (flowchart_id, step_number, sub_step), 
	FOREIGN KEY(flowchart_id) REFERENCES flowcharts (id), 
	FOREIGN KEY(technology_id) REFERENCES technologies (id), 
	FOREIGN KEY(machinery_id) REFERENCES machinery (id)
)

;
COMMENT ON COLUMN flowchart_steps.step_number IS 'e.g., 10, 20, 30. Used for ordering';
COMMENT ON COLUMN flowchart_steps.sub_step IS '0 for master step, 1, 2... for intermediate sub-steps';

CREATE TABLE pfmea_headers (
	id SERIAL NOT NULL, 
	flowchart_id BIGINT, 
	pfmea_id_number VARCHAR, 
	project_name TEXT, 
	customer TEXT, 
	original_launch_date DATE, 
	part_number TEXT, 
	product_description TEXT, 
	product_family_id BIGINT, 
	production_line_id BIGINT, 
	supplier_part_number TEXT, 
	model_year TEXT, 
	key_date DATE, 
	special_document_control TEXT DEFAULT '0', 
	process_responsibility TEXT, 
	moc_status VARCHAR DEFAULT 'Draft' NOT NULL, 
	plant_id BIGINT, 
	start_date DATE, 
	revision_date DATE, 
	confidentiality_level VARCHAR, 
	status VARCHAR, 
	owner_id BIGINT, 
	lock_version INTEGER DEFAULT '1' NOT NULL, 
	needs_review BOOLEAN DEFAULT 'false' NOT NULL, 
	version INTEGER DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(flowchart_id) REFERENCES flowcharts (id), 
	UNIQUE (pfmea_id_number), 
	FOREIGN KEY(product_family_id) REFERENCES product_families (id), 
	FOREIGN KEY(production_line_id) REFERENCES production_lines (id), 
	FOREIGN KEY(plant_id) REFERENCES plants (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
)

;
CREATE INDEX ix_pfmea_headers_flowchart_id ON pfmea_headers (flowchart_id);
COMMENT ON COLUMN pfmea_headers.flowchart_id IS 'Ties the FMEA to the approved process flow';
COMMENT ON COLUMN pfmea_headers.pfmea_id_number IS 'e.g. PUEBLA_PFMEA_001_2026_1';
COMMENT ON COLUMN pfmea_headers.moc_status IS 'Draft, In Review, Approved, Archived';
COMMENT ON COLUMN pfmea_headers.status IS 'Draft, In Review, Approved, Archived';

CREATE TABLE control_plans (
	id BIGSERIAL NOT NULL, 
	pfmea_project_id BIGINT NOT NULL, 
	flowchart_id BIGINT NOT NULL, 
	control_plan_code VARCHAR NOT NULL, 
	title VARCHAR NOT NULL, 
	owner_id BIGINT NOT NULL, 
	status VARCHAR DEFAULT 'Draft', 
	lock_version INTEGER DEFAULT '1' NOT NULL, 
	needs_review BOOLEAN DEFAULT 'false' NOT NULL, 
	version INTEGER DEFAULT '1' NOT NULL, 
	start_date DATE NOT NULL, 
	last_revision_date DATE, 
	created_by BIGINT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	observations VARCHAR, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pfmea_project_id) REFERENCES pfmea_headers (id), 
	FOREIGN KEY(flowchart_id) REFERENCES flowcharts (id), 
	UNIQUE (control_plan_code), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;
CREATE INDEX ix_control_plans_owner_id ON control_plans (owner_id);
CREATE INDEX ix_control_plans_pfmea_project_id ON control_plans (pfmea_project_id);
CREATE INDEX ix_control_plans_status ON control_plans (status);

CREATE TABLE pfmea_team_members (
	id SERIAL NOT NULL, 
	pfmea_id INTEGER, 
	user_id BIGINT, 
	role_in_team VARCHAR DEFAULT 'Team Member' NOT NULL, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	department VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_pfmea_team_pfmea_user UNIQUE (pfmea_id, user_id), 
	FOREIGN KEY(pfmea_id) REFERENCES pfmea_headers (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
COMMENT ON COLUMN pfmea_team_members.role_in_team IS 'PFMEA Owner, Team Member, Viewer';
COMMENT ON COLUMN pfmea_team_members.department IS 'Department of the member in the team';

CREATE TABLE pfmea_worksheet_rows (
	id BIGSERIAL NOT NULL, 
	pfmea_id BIGINT NOT NULL, 
	flowchart_step_id BIGINT, 
	process_item_name TEXT, 
	station_operation TEXT, 
	work_element_process TEXT, 
	operation_type TEXT, 
	function_process_item_plant TEXT, 
	function_process_item_customer TEXT, 
	function_process_item_end_user TEXT, 
	function_process_step TEXT, 
	product_characteristic TEXT, 
	function_work_element TEXT, 
	process_characteristic TEXT, 
	failure_mode TEXT, 
	failure_effect_plant TEXT, 
	failure_effect_customer TEXT, 
	failure_effect_end_user TEXT, 
	severity INTEGER, 
	failure_cause TEXT, 
	occurrence INTEGER, 
	prevention_controls TEXT, 
	detection_controls TEXT, 
	detection INTEGER, 
	action_priority VARCHAR, 
	special_characteristics TEXT, 
	optimization_prevention_action TEXT, 
	optimization_detection_action TEXT, 
	responsible_person_id BIGINT, 
	target_completion_date DATE, 
	action_status VARCHAR DEFAULT 'Open', 
	actions_taken TEXT, 
	completion_date DATE, 
	new_severity INTEGER, 
	new_occurrence INTEGER, 
	new_detection INTEGER, 
	new_action_priority VARCHAR, 
	validated_by BIGINT, 
	validated_at TIMESTAMP WITH TIME ZONE, 
	sequence_order INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pfmea_id) REFERENCES pfmea_headers (id) ON DELETE CASCADE, 
	FOREIGN KEY(flowchart_step_id) REFERENCES flowchart_steps (id) ON DELETE SET NULL, 
	FOREIGN KEY(responsible_person_id) REFERENCES users (id), 
	FOREIGN KEY(validated_by) REFERENCES users (id)
)

;
CREATE INDEX ix_worksheet_rows_pfmea_id ON pfmea_worksheet_rows (pfmea_id);
CREATE INDEX ix_worksheet_rows_action_priority ON pfmea_worksheet_rows (action_priority);
CREATE INDEX ix_worksheet_rows_flowchart_step ON pfmea_worksheet_rows (flowchart_step_id);
CREATE INDEX ix_worksheet_rows_responsible ON pfmea_worksheet_rows (responsible_person_id);
CREATE INDEX ix_worksheet_rows_action_status ON pfmea_worksheet_rows (action_status);
COMMENT ON COLUMN pfmea_worksheet_rows.process_item_name IS 'Process / subsystem name from flowchart';
COMMENT ON COLUMN pfmea_worksheet_rows.station_operation IS 'Station / operation name';
COMMENT ON COLUMN pfmea_worksheet_rows.work_element_process IS 'Step 2: Work Element Process (4M)';
COMMENT ON COLUMN pfmea_worksheet_rows.operation_type IS 'Technology / operation type';
COMMENT ON COLUMN pfmea_worksheet_rows.function_process_item_plant IS 'Step 3: Process item function (Plant)';
COMMENT ON COLUMN pfmea_worksheet_rows.function_process_item_customer IS 'Step 3: Process item function (Customer)';
COMMENT ON COLUMN pfmea_worksheet_rows.function_process_item_end_user IS 'Step 3: Process item function (End User)';
COMMENT ON COLUMN pfmea_worksheet_rows.function_process_step IS 'Step 3: Process step function / requirement';
COMMENT ON COLUMN pfmea_worksheet_rows.product_characteristic IS 'Step 3: Product characteristics (Optional)';
COMMENT ON COLUMN pfmea_worksheet_rows.function_work_element IS 'Step 3: Work element function';
COMMENT ON COLUMN pfmea_worksheet_rows.process_characteristic IS 'Step 3: Process characteristics (Optional)';
COMMENT ON COLUMN pfmea_worksheet_rows.failure_mode IS 'Step 4: Potential failure mode';
COMMENT ON COLUMN pfmea_worksheet_rows.failure_effect_plant IS 'Step 4: Effect of failure (Plant)';
COMMENT ON COLUMN pfmea_worksheet_rows.failure_effect_customer IS 'Step 4: Effect of failure (Customer)';
COMMENT ON COLUMN pfmea_worksheet_rows.failure_effect_end_user IS 'Step 4: Effect of failure (End User)';
COMMENT ON COLUMN pfmea_worksheet_rows.severity IS 'Severity rating 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.failure_cause IS 'Step 4: Potential cause of failure';
COMMENT ON COLUMN pfmea_worksheet_rows.occurrence IS 'Occurrence rating 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.prevention_controls IS 'Step 5: Current prevention controls';
COMMENT ON COLUMN pfmea_worksheet_rows.detection_controls IS 'Step 5: Current detection controls';
COMMENT ON COLUMN pfmea_worksheet_rows.detection IS 'Detection rating 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.action_priority IS 'Auto-calculated: H, M, L (AIAG-VDA AP)';
COMMENT ON COLUMN pfmea_worksheet_rows.special_characteristics IS 'Step 5: Special Characteristics';
COMMENT ON COLUMN pfmea_worksheet_rows.optimization_prevention_action IS 'Step 6: Recommended prevention action';
COMMENT ON COLUMN pfmea_worksheet_rows.optimization_detection_action IS 'Step 6: Recommended detection action';
COMMENT ON COLUMN pfmea_worksheet_rows.action_status IS 'Open, In Progress, Completed';
COMMENT ON COLUMN pfmea_worksheet_rows.new_severity IS 'Re-evaluated severity 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.new_occurrence IS 'Re-evaluated occurrence 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.new_detection IS 'Re-evaluated detection 1-10';
COMMENT ON COLUMN pfmea_worksheet_rows.new_action_priority IS 'Re-evaluated AP: H, M, L';

CREATE TABLE process_items (
	id SERIAL NOT NULL, 
	pfmea_id INTEGER, 
	item_name VARCHAR, 
	description TEXT, 
	sequence_order INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pfmea_id) REFERENCES pfmea_headers (id)
)

;
COMMENT ON COLUMN process_items.item_name IS 'System, Subsystem, Part, or Process Name';

CREATE TABLE document_audit_logs (
	id BIGSERIAL NOT NULL, 
	flowchart_id BIGINT, 
	pfmea_project_id BIGINT, 
	control_plan_id BIGINT, 
	operation_instruction_sheet_id BIGINT, 
	action VARCHAR NOT NULL, 
	performed_by BIGINT NOT NULL, 
	action_details VARCHAR, 
	previous_values JSONB, 
	new_values JSONB, 
	performed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	entity_type TEXT, 
	entity_id BIGINT, 
	field_name TEXT, 
	old_value TEXT, 
	new_value TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(flowchart_id) REFERENCES flowcharts (id), 
	FOREIGN KEY(pfmea_project_id) REFERENCES pfmea_headers (id), 
	FOREIGN KEY(control_plan_id) REFERENCES control_plans (id), 
	FOREIGN KEY(operation_instruction_sheet_id) REFERENCES instruction_sheets (id), 
	FOREIGN KEY(performed_by) REFERENCES users (id)
)

;
CREATE INDEX ix_audit_logs_performed_by ON document_audit_logs (performed_by);
CREATE INDEX ix_audit_logs_entity ON document_audit_logs (entity_type, entity_id);
CREATE INDEX ix_audit_logs_performed_at ON document_audit_logs (performed_at);
COMMENT ON COLUMN document_audit_logs.entity_type IS 'e.g. pfmea_header, pfmea_worksheet_row, pfmea_team_member';
COMMENT ON COLUMN document_audit_logs.entity_id IS 'PK of the affected entity';
COMMENT ON COLUMN document_audit_logs.field_name IS 'Name of the modified column';
COMMENT ON COLUMN document_audit_logs.old_value IS 'Previous value (serialised to text)';
COMMENT ON COLUMN document_audit_logs.new_value IS 'New value (serialised to text)';

CREATE TABLE control_plan_items (
	id BIGSERIAL NOT NULL, 
	control_plan_id BIGINT NOT NULL, 
	process_failure_mode_id BIGINT, 
	process_parameter_control_id BIGINT, 
	item_sequence INTEGER NOT NULL, 
	item_name VARCHAR NOT NULL, 
	pfmea_worksheet_row_id BIGINT, 
	source_row_id BIGINT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	source_reviewed BOOLEAN DEFAULT 'false' NOT NULL, 
	source_review_reason VARCHAR, 
	needs_review BOOLEAN DEFAULT 'false' NOT NULL, 
	characteristic VARCHAR, 
	classification VARCHAR(2), 
	specification VARCHAR, 
	unit_id BIGINT, 
	measurement_method VARCHAR, 
	sample_size INTEGER, 
	sample_frequency VARCHAR, 
	responsible_person_id BIGINT, 
	reaction_plan VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(control_plan_id) REFERENCES control_plans (id), 
	FOREIGN KEY(process_failure_mode_id) REFERENCES process_failure_modes (id), 
	FOREIGN KEY(process_parameter_control_id) REFERENCES process_parameter_controls (id), 
	FOREIGN KEY(pfmea_worksheet_row_id) REFERENCES pfmea_worksheet_rows (id) ON DELETE SET NULL, 
	FOREIGN KEY(unit_id) REFERENCES measurement_units (id), 
	FOREIGN KEY(responsible_person_id) REFERENCES users (id)
)

;

CREATE TABLE process_steps (
	id SERIAL NOT NULL, 
	process_item_id INTEGER, 
	station_number VARCHAR, 
	step_name VARCHAR, 
	sequence_order INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(process_item_id) REFERENCES process_items (id)
)

;
COMMENT ON COLUMN process_steps.step_name IS 'Name of Focus Element';

CREATE TABLE control_plan_reactions (
	id BIGSERIAL NOT NULL, 
	control_plan_item_id BIGINT NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(control_plan_item_id) REFERENCES control_plan_items (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE control_point_characteristics (
	id BIGSERIAL NOT NULL, 
	control_plan_item_id BIGINT NOT NULL, 
	name VARCHAR NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	deleted_at TIMESTAMP WITHOUT TIME ZONE, 
	deleted_by BIGINT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(control_plan_item_id) REFERENCES control_plan_items (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
)

;

CREATE TABLE process_work_elements (
	id SERIAL NOT NULL, 
	process_step_id INTEGER, 
	element_type VARCHAR, 
	description TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(process_step_id) REFERENCES process_steps (id)
)

;
COMMENT ON COLUMN process_work_elements.element_type IS 'Machine, Man, Material (Indirect), Environment';
ALTER TABLE departments ADD FOREIGN KEY(deleted_by) REFERENCES users (id);
ALTER TABLE users ADD FOREIGN KEY(deleted_by) REFERENCES users (id);
ALTER TABLE users ADD FOREIGN KEY(plant_id) REFERENCES plants (id);
ALTER TABLE plants ADD FOREIGN KEY(deleted_by) REFERENCES users (id);
ALTER TABLE regions ADD FOREIGN KEY(deleted_by) REFERENCES users (id);
ALTER TABLE users ADD FOREIGN KEY(department_id) REFERENCES departments (id);
ALTER TABLE users ADD FOREIGN KEY(role_id) REFERENCES roles (id);
ALTER TABLE plants ADD FOREIGN KEY(region_id) REFERENCES regions (id);
ALTER TABLE roles ADD FOREIGN KEY(deleted_by) REFERENCES users (id);