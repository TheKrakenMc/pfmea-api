CREATE TABLE "roles" (
  "id" serial PRIMARY KEY,
  "name" varchar UNIQUE
);

CREATE TABLE "regions" (
  "id" serial PRIMARY KEY,
  "name" varchar UNIQUE
);

CREATE TABLE "plants" (
  "id" serial PRIMARY KEY,
  "region_id" int,
  "name" varchar,
  "code" varchar UNIQUE,
  "is_active" boolean DEFAULT true
);

CREATE TABLE "users" (
  "id" serial PRIMARY KEY,
  "role_id" int,
  "plant_id" int,
  "full_name" varchar,
  "email" varchar UNIQUE,
  "is_active" boolean DEFAULT true,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "products" (
  "id" serial PRIMARY KEY,
  "plant_id" int,
  "customer_name" varchar,
  "part_number" varchar,
  "description" text
);

CREATE TABLE "technologies" (
  "id" serial PRIMARY KEY,
  "plant_id" int,
  "operation_name" varchar
);

CREATE TABLE "flowcharts" (
  "id" serial PRIMARY KEY,
  "product_id" int,
  "owner_id" int,
  "title" varchar,
  "version" int DEFAULT 1,
  "status" varchar,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp DEFAULT (now())
);

CREATE TABLE "flowchart_steps" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int,
  "technology_id" int,
  "step_number" int,
  "custom_description" varchar
);

CREATE TABLE "pfmea_headers" (
  "id" serial PRIMARY KEY,
  "flowchart_id" int,
  "pfmea_id_number" varchar UNIQUE,
  "start_date" date,
  "revision_date" date,
  "confidentiality_level" varchar,
  "status" varchar,
  "owner_id" int,
  "version" int DEFAULT 1,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp DEFAULT (now())
);

CREATE TABLE "pfmea_team_members" (
  "id" serial PRIMARY KEY,
  "pfmea_id" int,
  "user_id" int,
  "assigned_at" timestamp DEFAULT (now())
);

CREATE TABLE "process_items" (
  "id" serial PRIMARY KEY,
  "pfmea_id" int,
  "item_name" varchar,
  "description" text,
  "sequence_order" int
);

CREATE TABLE "process_steps" (
  "id" serial PRIMARY KEY,
  "process_item_id" int,
  "station_number" varchar,
  "step_name" varchar,
  "sequence_order" int
);

CREATE TABLE "process_work_elements" (
  "id" serial PRIMARY KEY,
  "process_step_id" int,
  "element_type" varchar,
  "description" text
);

CREATE UNIQUE INDEX ON "products" ("plant_id", "part_number");

CREATE UNIQUE INDEX ON "technologies" ("plant_id", "operation_name");

CREATE INDEX ON "flowcharts" ("product_id");

CREATE UNIQUE INDEX ON "flowchart_steps" ("flowchart_id", "step_number");

CREATE INDEX ON "pfmea_headers" ("flowchart_id");

CREATE UNIQUE INDEX ON "pfmea_team_members" ("pfmea_id", "user_id");

COMMENT ON COLUMN "roles"."name" IS 'Administrator, PFMEA Owner, Team Member, Viewer';

COMMENT ON COLUMN "regions"."name" IS 'e.g., NAFTA, EMEA, APAC';

COMMENT ON COLUMN "plants"."code" IS 'e.g., OREGON, BOCHUM, PUEBLA';

COMMENT ON COLUMN "users"."plant_id" IS 'Primary location of the user';

COMMENT ON COLUMN "products"."customer_name" IS 'e.g., Ford, Tesla, VW';

COMMENT ON COLUMN "technologies"."operation_name" IS 'e.g., AirLay, Assembly, PU Foaming';

COMMENT ON COLUMN "flowcharts"."status" IS 'Draft, Approved, Archived';

COMMENT ON COLUMN "flowchart_steps"."step_number" IS 'e.g., 10, 20, 30. Used for ordering';

COMMENT ON COLUMN "flowchart_steps"."custom_description" IS 'Specific detail for this product step';

COMMENT ON COLUMN "pfmea_headers"."flowchart_id" IS 'Ties the FMEA to the approved process flow';

COMMENT ON COLUMN "pfmea_headers"."pfmea_id_number" IS 'e.g. OREGON_PFMEA_059_2026_1';

COMMENT ON COLUMN "pfmea_headers"."status" IS 'Draft, Submitted for Review, Approved, Archived';

COMMENT ON COLUMN "process_items"."item_name" IS 'System, Subsystem, Part, or Process Name';

COMMENT ON COLUMN "process_steps"."step_name" IS 'Name of Focus Element';

COMMENT ON COLUMN "process_work_elements"."element_type" IS 'Machine, Man, Material (Indirect), Environment';

ALTER TABLE "plants" ADD FOREIGN KEY ("region_id") REFERENCES "regions" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "users" ADD FOREIGN KEY ("role_id") REFERENCES "roles" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "users" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "products" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "technologies" ADD FOREIGN KEY ("plant_id") REFERENCES "plants" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("product_id") REFERENCES "products" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowcharts" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_steps" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "flowchart_steps" ADD FOREIGN KEY ("technology_id") REFERENCES "technologies" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_headers" ADD FOREIGN KEY ("flowchart_id") REFERENCES "flowcharts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_headers" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_team_members" ADD FOREIGN KEY ("pfmea_id") REFERENCES "pfmea_headers" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "pfmea_team_members" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_items" ADD FOREIGN KEY ("pfmea_id") REFERENCES "pfmea_headers" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_steps" ADD FOREIGN KEY ("process_item_id") REFERENCES "process_items" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "process_work_elements" ADD FOREIGN KEY ("process_step_id") REFERENCES "process_steps" ("id") DEFERRABLE INITIALLY IMMEDIATE;
