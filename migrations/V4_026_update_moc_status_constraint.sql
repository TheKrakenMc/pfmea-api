-- Migration: Update ck_pfmea_headers_moc_status constraint to support 'In Review'
-- Fixes CheckViolationError when transitioning PFMEA MOC status from Draft to In Review.

ALTER TABLE pfmea_headers DROP CONSTRAINT IF EXISTS ck_pfmea_headers_moc_status;

ALTER TABLE pfmea_headers
    ADD CONSTRAINT ck_pfmea_headers_moc_status
    CHECK (moc_status IN ('Draft', 'In Review', 'Submitted for Review', 'Approved', 'Archived'));
