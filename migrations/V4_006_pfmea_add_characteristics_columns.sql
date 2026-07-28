-- V4_006_pfmea_add_characteristics_columns.sql
-- Adición de las columnas de características opcionales para el Paso 3.

ALTER TABLE pfmea_worksheet_rows
ADD COLUMN product_characteristic TEXT,
ADD COLUMN process_characteristic TEXT;
