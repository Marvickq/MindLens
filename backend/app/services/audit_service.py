"""
Audit Service
Immutable audit trail for important system actions.
"""
import uuid
from typing import Optional, Any

from sqlmodel import Session, select

from app.models.audit_event import AuditEvent, ActorType


def create_audit_event(
    case_id: Optional[uuid.UUID],
    actor_type: ActorType,
    actor_id: Optional[uuid.UUID],
    event_type: str,
    metadata: dict,
    db: Session,
) -> AuditEvent:
    event = AuditEvent(
        case_id=case_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        event_metadata=metadata,
    )
    db.add(event)
    db.flush()
    return event


def get_audit_events(case_id: uuid.UUID, db: Session) -> list[AuditEvent]:
    return db.exec(
        select(AuditEvent)
        .where(AuditEvent.case_id == case_id)
        .order_by(AuditEvent.created_at.desc())
    ).all()
