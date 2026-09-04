import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class CaseStatus(str, Enum):
    WAITING_FOR_RESPONSES = "WAITING_FOR_RESPONSES"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class StudentCase(SQLModel, table=True):
    __tablename__ = "student_cases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organizations.id")
    external_reference: Optional[str] = Field(default=None, max_length=255)
    display_name: str = Field(max_length=255)
    grade: Optional[str] = Field(default=None, max_length=50)
    school: Optional[str] = Field(default=None, max_length=255)
    status: CaseStatus = Field(default=CaseStatus.WAITING_FOR_RESPONSES)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
