import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class Response(SQLModel, table=True):
    __tablename__ = "responses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="rater_sessions.id")
    question_id: uuid.UUID = Field(foreign_key="questions.id")
    value: Any = Field(sa_column=Column(JSON, nullable=False))  # JSONB — Likert/int/bool/text
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
