import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class CaseCustomQuestion(SQLModel, table=True):
    """
    Counselor-led personalization for a FUTURE session.

    A counselor may opt in additional questions/modules. These selections ADDTO
    -- and never replace, remove, or modify -- the six permanent core
    dimensions. There is no automatic/AI selection: the choice is always made
    by a counselor.

    Because a future session has not been generated yet, this is purely a
    declarative backend record of the counselor's intent. The intake/QR
    workflow and current questionnaire are intentionally untouched.
    """
    __tablename__ = "case_custom_questions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    question_id: uuid.UUID = Field(foreign_key="questions.id")

    # Which rater's future session this targets. When NULL it applies to all
    # rater perspectives.
    rater_type: Optional[str] = Field(default=None, max_length=50)

    selected_by: uuid.UUID = Field(foreign_key="users.id")
    rationale: Optional[str] = None
    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
