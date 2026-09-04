-- MindLens migration 002
-- Add token encryption columns to rater_sessions so raw intake tokens and
-- intake URLs can be recovered (to regenerate QR codes / resend links) after
-- restart, without ever persisting the raw token in plaintext.
--
-- The raw token is still only ever stored as SHA-256 (token_hash); these new
-- columns hold a Fernet-encrypted copy keyed by TOKEN_ENCRYPTION_KEY (env).

ALTER TABLE rater_sessions
    ADD COLUMN IF NOT EXISTS encrypted_token      TEXT,
    ADD COLUMN IF NOT EXISTS encrypted_intake_url TEXT;
