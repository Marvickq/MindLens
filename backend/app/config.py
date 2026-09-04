from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import sys


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = ""
    jwt_secret: str = ""
    jwt_expiry_minutes: int = 60
    intake_token_ttl_hours: int = 72
    environment: str = "development"
    rate_limit_requests: int = 10
    rate_limit_period: int = 60

    # Public base URL used to build real, scannable rater intake URLs
    # (e.g. https://app.MindLens.example). Must never be localhost in prod.
    frontend_public_url: str = ""

    # AI API key for analysis
    grok_api_key: str | None = None

    # Fernet key (44-char urlsafe base64) used to encrypt the raw intake token
    # and intake URL so QRs/links can be regenerated without ever persisting
    # the raw token in plaintext. MUST come from the environment, not source.
    token_encryption_key: str = ""


@lru_cache()
def get_settings() -> Settings:
    s = Settings()

    # Production guard: fail-fast when critical env vars are missing or insecure.
    # Enforce when ENVIRONMENT=production AND we appear to have real env vars set.
    # Skip when _test_mode is active (set by test setup before first settings use).
    if s.environment == "production" and s.database_url and not _test_mode:
        _reasons = []

        if not s.jwt_secret:
            _reasons.append("JWT_SECRET")
        if not s.token_encryption_key:
            _reasons.append("TOKEN_ENCRYPTION_KEY")
        if "localhost" in (s.frontend_public_url or ""):
            _reasons.append("FRONTEND_PUBLIC_URL is localhost")
        if "localhost" in (s.database_url or ""):
            _reasons.append("DATABASE_URL is localhost")

        if _reasons:
            msg = (
                "REFUSING TO BOOT IN PRODUCTION: missing or insecure config. "
                f"Required env vars not set: {', '.join(_reasons)}. "
                "Set these in the environment before starting."
            )
            print(f"\nFATAL: {msg}\n", file=sys.stderr)
            sys.exit(1)

    return s


_test_mode = False


def set_test_mode():
    """Mark that the production config guard should be bypassed (test env)."""
    global _test_mode
    _test_mode = True
