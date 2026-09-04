import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class CounselorAction(str, Enum):
    MONITOR = "MONITOR"
    REACH_OUT = "REACH_OUT"
    REFER = "REFER"


class CounselorReview(SQLModel, table=True):
    __tablename__ = "counselor_reviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    counselor_id: uuid.UUID = Field(foreign_key="users.id")
    action: CounselorAction
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
