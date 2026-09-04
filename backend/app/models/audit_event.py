import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class ActorType(str, Enum):
    COUNSELOR = "COUNSELOR"
    ADMIN = "ADMIN"
    RATER = "RATER"
    SYSTEM = "SYSTEM"


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: Optional[uuid.UUID] = Field(default=None, foreign_key="student_cases.id")
    actor_type: ActorType
    actor_id: Optional[uuid.UUID] = None
    event_type: str = Field(max_length=100)
    event_metadata: Any = Field(default={}, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
