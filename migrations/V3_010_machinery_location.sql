ALTER TABLE pfmea.machinery
ADD COLUMN location_id BIGINT REFERENCES pfmea.manufacturing_locations(id) ON DELETE SET NULL;
