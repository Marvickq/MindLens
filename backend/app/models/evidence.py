import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Evidence(SQLModel, table=True):
    __tablename__ = "evidence"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    evidence_code: str = Field(max_length=100, unique=True)
    dimension_id: Optional[uuid.UUID] = Field(default=None, foreign_key="dimensions.id")
    rater_pair: Optional[str] = Field(default=None, max_length=50)  # e.g. PARENT_TEACHER
    title: str = Field(max_length=500)
    source: str
    source_type: Optional[str] = Field(default=None, max_length=100)
    citation: Optional[str] = None
    evidence_certainty: Optional[str] = Field(default=None, max_length=100)
    study_count: Optional[int] = None
    sample_size: Optional[int] = None
    association_value: Optional[str] = None
    limitation: Optional[str] = None
    version: str = Field(default="1.0", max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
