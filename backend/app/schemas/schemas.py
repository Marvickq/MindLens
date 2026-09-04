from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

from app.models.counselor_review import CounselorAction


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    role: str


class CaseCreate(BaseModel):
    display_name: str
    grade: Optional[str] = None
    school: Optional[str] = None
    external_reference: Optional[str] = None


class CaseSummary(BaseModel):
    id: UUID
    display_name: str
    external_reference: Optional[str]
    grade: Optional[str]
    school: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class CaseSessionInfo(BaseModel):
    rater_type: str
    status: str
    submitted_at: Optional[datetime] = None


class CaseDetail(BaseModel):
    id: UUID
    display_name: str
    external_reference: Optional[str]
    grade: Optional[str]
    school: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    sessions: List[CaseSessionInfo]
    review: Optional[Any] = None


class DashboardSummary(BaseModel):
    awaiting_responses: int
    ready_for_review: int
    under_review: int
    completed: int


class IntakeResponseSubmit(BaseModel):
    question_id: UUID
    value: Any


class ReviewSubmit(BaseModel):
    action: CounselorAction
    note: Optional[str] = None


class IntakeSessionInfo(BaseModel):
    rater_type: str
    status: str
    intake_url: Optional[str] = None
    token: Optional[str] = None
    qr_payload: Optional[dict] = None


class CaseCreationResponse(BaseModel):
    case_id: UUID
    display_name: str
    status: str
    grade: Optional[str] = None
    school: Optional[str] = None
    sessions: List[IntakeSessionInfo]


class HeatmapCell(BaseModel):
    dimension_id: str
    dimension_label: str
    dimension_code: str
    rater_type: str
    score: Optional[float] = None
    has_response: bool = False


class HeatmapResponse(BaseModel):
    dimensions: List[dict]
    raters: List[str]
    cells: List[HeatmapCell]


class AuditEventSummary(BaseModel):
    id: UUID
    event_type: str
    actor_type: str
    event_metadata: Any
    created_at: datetime


class PresentedAuditEvent(BaseModel):
    id: UUID
    event_type: str
    actor: str
    actor_type: str
    rater_type: Optional[str] = None
    category: str
    display_title: str
    description: str
    technical: bool
    occurred_at: datetime
    metadata: Any


class PresentedAuditTrail(BaseModel):
    timeline: List[PresentedAuditEvent]
    technical: List[PresentedAuditEvent]
    assessment_history: dict
