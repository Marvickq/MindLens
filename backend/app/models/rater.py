import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class RaterType(str, Enum):
    PARENT = "PARENT"
    TEACHER = "TEACHER"
    ADOLESCENT = "ADOLESCENT"


class SessionStatus(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class RaterSession(SQLModel, table=True):
    __tablename__ = "rater_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    rater_type: RaterType
    token_hash: str = Field(unique=True)  # SHA-256 of public token — never store raw
    # Fernet-encrypted raw token + intake URL (keyed by TOKEN_ENCRYPTION_KEY).
    # Allows QR/link regeneration without storing the raw token in plaintext.
    encrypted_token: Optional[str] = None
    encrypted_intake_url: Optional[str] = None
    status: SessionStatus = Field(default=SessionStatus.CREATED)
    expires_at: datetime
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
