"""
Review Service
Handles counselor actions (MONITOR, REACH_OUT, REFER) and notes.
The backend NEVER automatically chooses an action.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.counselor_review import CounselorReview, CounselorAction
from app.models.case import StudentCase, CaseStatus
from app.models.audit_event import AuditEvent, ActorType


def create_counselor_review(
    case_id: uuid.UUID,
    counselor_id: uuid.UUID,
    action: CounselorAction,
    note: Optional[str],
    db: Session,
) -> CounselorReview:
    case = db.get(StudentCase, case_id)
    if not case:
        raise ValueError("Student case not found.")

    review = CounselorReview(
        case_id=case_id,
        counselor_id=counselor_id,
        action=action,
        note=note,
    )
    db.add(review)

    # Update case status based on review creation
    case.status = CaseStatus.UNDER_REVIEW if action == CounselorAction.MONITOR else CaseStatus.COMPLETED
    case.updated_at = datetime.now(timezone.utc)
    db.add(case)

    # Immutable Audit Event
    audit = AuditEvent(
        case_id=case_id,
        actor_type=ActorType.COUNSELOR,
        actor_id=counselor_id,
        event_type="REVIEW_CREATED",
        event_metadata={"action": action.value, "note_length": len(note) if note else 0},
    )
    db.add(audit)

    db.commit()
    db.refresh(review)
    return review


def get_counselor_review(case_id: uuid.UUID, db: Session) -> Optional[CounselorReview]:
    return db.exec(
        select(CounselorReview)
        .where(CounselorReview.case_id == case_id)
        .order_by(CounselorReview.created_at.desc())
    ).first()
