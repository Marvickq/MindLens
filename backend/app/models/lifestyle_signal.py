import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class LifestyleSignal(SQLModel, table=True):
    __tablename__ = "lifestyle_signals"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    factor: str = Field(max_length=255)
    observed_response: Any = Field(sa_column=Column(JSON, nullable=False))
    evidence_id: Optional[uuid.UUID] = Field(default=None, foreign_key="evidence.id")
    association_value: Optional[str] = None
    certainty: Optional[str] = Field(default=None, max_length=100)
    limitation: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
