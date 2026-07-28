-- Add safety_characteristic column to customers
ALTER TABLE pfmea.customers ADD COLUMN IF NOT EXISTS safety_characteristic VARCHAR NOT NULL DEFAULT 'D';
