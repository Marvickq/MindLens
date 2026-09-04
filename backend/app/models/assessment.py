import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class ResponseType(str, Enum):
    LIKERT = "LIKERT"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"
    SINGLE_CHOICE = "SINGLE_CHOICE"


class AssessmentVersion(SQLModel, table=True):
    __tablename__ = "assessment_versions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    version: str = Field(max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Dimension(SQLModel, table=True):
    __tablename__ = "dimensions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dimension_code: str = Field(max_length=100, unique=True)
    label: str = Field(max_length=255)
    description: Optional[str] = None
    display_order: int
    active: bool = Field(default=True)


class Question(SQLModel, table=True):
    __tablename__ = "questions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    assessment_version_id: uuid.UUID = Field(foreign_key="assessment_versions.id")
    dimension_id: uuid.UUID = Field(foreign_key="dimensions.id")
    question_code: str = Field(max_length=100)
    question_text: str
    response_type: ResponseType
    required: bool = Field(default=True)
    display_order: int
    validation_config: Optional[Any] = Field(default={}, sa_column=Column(JSON))
    active: bool = Field(default=True)
