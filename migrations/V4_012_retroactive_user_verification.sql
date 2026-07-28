-- Migration V4_012_retroactive_user_verification
-- Establecer usuarios existentes como verificados y sin requerimiento de cambio de contraseña
-- para evitar bloqueos en cuentas previas a la implementación de TISAX.
UPDATE users SET is_verified = TRUE, must_change_password = FALSE;
