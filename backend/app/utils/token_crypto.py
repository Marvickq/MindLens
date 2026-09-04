"""
Token encryption helpers.

The raw rater intake token must never be stored in plaintext -- the database
keeps only its SHA-256 hash (`token_hash`). To allow a counselor to regenerate
a QR code or resend an intake link after the process restarts (when the
in-memory token store is gone), we symmetrically encrypt the raw token with a
Fernet key loaded from `TOKEN_ENCRYPTION_KEY` in the environment.

Security model:
  - Raw token is only ever transmitted once at creation, or re-derived by
    decrypting `encrypted_token`.
  - `TOKEN_ENCRYPTION_KEY` is a secret, loaded from env -- never committed.
  - The encrypted blob is useless without the key and is not the token itself.
"""
import hashlib
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def _get_fernet():
    from cryptography.fernet import Fernet

    key = (settings.token_encryption_key or "").strip()
    if not key:
        # Dev/test fallback only: derive a stable key from the JWT secret so
        # in-memory SQLite tests and local dev work without a real key set.
        # Production MUST set TOKEN_ENCRYPTION_KEY.
        if settings.environment == "production":
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY must be set in production. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        key = hashlib.sha256(settings.jwt_secret.encode()).digest()
        key = __import__("base64").b64encode(key).decode()
    return Fernet(key.encode())


def encrypt_value(plaintext: str) -> str:
    """Return a Fernet token (urlsafe str) for the given plaintext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Return the plaintext for a Fernet-encrypted value."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def build_intake_url(raw_token: str) -> str:
    """Build the canonical public intake URL for a raw token.

    Uses `FRONTEND_PUBLIC_URL` if configured, otherwise falls back to a
    localhost default for local development. Production must set
    `FRONTEND_PUBLIC_URL` so scanned links resolve to the real frontend.
    """
    base = (settings.frontend_public_url or "").rstrip("/")
    if not base:
        base = "http://localhost:3000"
        if settings.environment == "production":
            logger.warning(
                "FRONTEND_PUBLIC_URL is not set in production; intake links "
                "will not be scannable from other devices."
            )
    return f"{base}/intake/{raw_token}"
