import uuid
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class DimensionScore(SQLModel, table=True):
    __tablename__ = "dimension_scores"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    rater_type: str  # RaterType enum value
    dimension_id: uuid.UUID = Field(foreign_key="dimensions.id")
    score: float
    questionnaire_version: str = Field(max_length=50)
    calculation_method: str = Field(max_length=100)
    calculation_version: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
