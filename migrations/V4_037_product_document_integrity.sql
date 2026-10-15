ALTER TABLE pfmea.products ADD COLUMN lock_version integer NOT NULL DEFAULT 1;
ALTER TABLE pfmea.products ADD COLUMN needs_review boolean NOT NULL DEFAULT false;
-- Preserve released documents and their contents; flag them rather than rebuilding history.
UPDATE pfmea.products SET needs_review=true WHERE status='Released';
