-- Migration: V3_002_security_and_otps
-- Description: Add password_hash to users and create user_otps table for 2-phase auth.

-- 1. Add password_hash column to users table
ALTER TABLE pfmea.users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- 2. Create user_otps table
CREATE TABLE IF NOT EXISTS pfmea.user_otps (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_user_otps_user FOREIGN KEY (user_id) REFERENCES pfmea.users(id) ON DELETE CASCADE
);

-- 3. Create indices for performance
CREATE INDEX IF NOT EXISTS idx_user_otps_user_id ON pfmea.user_otps(user_id);
CREATE INDEX IF NOT EXISTS idx_user_otps_code ON pfmea.user_otps(otp_code);
