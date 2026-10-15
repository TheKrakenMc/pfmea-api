-- Recovery codes are stored as purpose-bound HMAC digests, never plaintext.
ALTER TABLE pfmea.user_otps ALTER COLUMN otp_code TYPE text;
-- Additive upgrade: preserves documents and revokes legacy authentication.
CREATE TABLE IF NOT EXISTS auth_sessions (
 id varchar(64) PRIMARY KEY, user_id bigint NOT NULL REFERENCES users(id),
 refresh_hash varchar(64) NOT NULL, csrf_token varchar(128) NOT NULL,
 expires_at timestamptz NOT NULL, revoked boolean NOT NULL DEFAULT false);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE TABLE IF NOT EXISTS user_plants (
 user_id bigint NOT NULL REFERENCES users(id), plant_id bigint NOT NULL REFERENCES plants(id),
 PRIMARY KEY(user_id, plant_id));
CREATE TABLE IF NOT EXISTS used_verification_tokens (
 token_hash varchar(64) PRIMARY KEY, user_id bigint NOT NULL REFERENCES users(id));
INSERT INTO user_plants SELECT id, plant_id FROM users WHERE plant_id IS NOT NULL ON CONFLICT DO NOTHING;
INSERT INTO user_plants SELECT owner_id, plant_id FROM pfmea_headers WHERE owner_id IS NOT NULL AND plant_id IS NOT NULL ON CONFLICT DO NOTHING;
INSERT INTO user_plants SELECT t.user_id, h.plant_id FROM pfmea_team_members t JOIN pfmea_headers h ON h.id=t.pfmea_id WHERE h.plant_id IS NOT NULL ON CONFLICT DO NOTHING;
INSERT INTO user_plants SELECT created_by, plant_id FROM flowcharts WHERE created_by IS NOT NULL AND plant_id IS NOT NULL ON CONFLICT DO NOTHING;
UPDATE users u SET plant_id=(SELECT min(p.plant_id) FROM user_plants p WHERE p.user_id=u.id) WHERE u.plant_id IS NULL;
UPDATE user_otps SET is_used=true;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS lock_version integer NOT NULL DEFAULT 1;
ALTER TABLE pfmea_headers ADD COLUMN IF NOT EXISTS needs_review boolean NOT NULL DEFAULT false;
ALTER TABLE flowcharts ADD COLUMN IF NOT EXISTS lock_version integer NOT NULL DEFAULT 1;
ALTER TABLE flowcharts ADD COLUMN IF NOT EXISTS needs_review boolean NOT NULL DEFAULT false;
ALTER TABLE control_plans ADD COLUMN IF NOT EXISTS lock_version integer NOT NULL DEFAULT 1;
ALTER TABLE control_plans ADD COLUMN IF NOT EXISTS needs_review boolean NOT NULL DEFAULT false;
ALTER TABLE pfmea_worksheet_rows ADD COLUMN IF NOT EXISTS validated_by bigint REFERENCES users(id);
ALTER TABLE pfmea_worksheet_rows ADD COLUMN IF NOT EXISTS validated_at timestamptz;
UPDATE pfmea_headers h SET needs_review=true WHERE moc_status IN ('Approved','Archived') AND EXISTS (
 SELECT 1 FROM pfmea_worksheet_rows r WHERE r.pfmea_id=h.id AND (r.action_priority='H' OR r.severity>=9) AND r.validated_by IS NULL);
