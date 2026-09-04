"""
Intake Service
Handles: token generation, questionnaire retrieval, response saving, session locking.
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.rater import RaterSession, RaterType, SessionStatus
from app.models.assessment import Question
from app.models.response import Response
from app.models.case import StudentCase, CaseStatus
from app.models.audit_event import AuditEvent, ActorType
from app.config import get_settings
from app.utils.token_crypto import (
    encrypt_value,
    decrypt_value,
    build_intake_url,
)
from app.utils.qr import generate_qr_payload

settings = get_settings()

CALCULATION_VERSION = "1.0"
QUESTIONNAIRE_VERSION = "1.0"

# Presentational status labels exposed to the frontend. The database keeps the
# SessionStatus enum (CREATED/STARTED/SUBMITTED/EXPIRED/REVOKED) as source of
# truth; these are user-facing mappings only.
STATUS_LABEL_MAP = {
    SessionStatus.CREATED: "PENDING",
    SessionStatus.STARTED: "IN_PROGRESS",
    SessionStatus.SUBMITTED: "SUBMITTED",
    SessionStatus.EXPIRED: "EXPIRED",
    SessionStatus.REVOKED: "REVOKED",
}


def status_label(session: RaterSession) -> str:
    return STATUS_LABEL_MAP.get(session.status, session.status.value)


def build_session_info(session: RaterSession) -> dict:
    """Sanitized, public-facing session descriptor (intake_url included)."""
    return {
        "id": str(session.id),
        "rater_type": session.rater_type.value,
        "status": status_label(session),
        "submitted_at": session.submitted_at,
        "expires_at": session.expires_at,
        "intake_url": get_intake_url(session),
    }


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_intake_sessions(
    case_id: uuid.UUID,
    db: Session,
) -> list[dict]:
    """
    Generate one intake session per rater type.
    Returns list of {rater_type, session_id, token (plaintext), intake_url, qr_payload}.
    The plaintext token is returned once only — only the SHA-256 hash plus a
    Fernet-encrypted copy are persisted.
    """
    results = []
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.intake_token_ttl_hours)

    for rater in RaterType:
        existing = db.exec(
            select(RaterSession).where(
                RaterSession.case_id == case_id,
                RaterSession.rater_type == rater,
            )
        ).first()
        if existing:
            continue

        raw_token = _generate_token()
        token_hash = _hash_token(raw_token)
        intake_url = build_intake_url(raw_token)

        session = RaterSession(
            case_id=case_id,
            rater_type=rater,
            token_hash=token_hash,
            encrypted_token=encrypt_value(raw_token),
            encrypted_intake_url=encrypt_value(intake_url),
            expires_at=expires_at,
        )
        db.add(session)
        db.flush()

        qr_payload = generate_qr_payload(intake_url)
        results.append({
            "session_id": str(session.id),
            "rater_type": rater.value,
            "token": raw_token,
            "intake_url": intake_url,
            "qr_payload": qr_payload,
        })

    return results


def get_intake_url(session: RaterSession) -> Optional[str]:
    """Return the intake URL for a session, decrypting it if necessary."""
    if session.encrypted_intake_url:
        try:
            return decrypt_value(session.encrypted_intake_url)
        except Exception:
            return None
    return None


def generate_qr_for_session(session: RaterSession) -> Optional[dict]:
    """Re-generate the QR payload for a session from its stored intake URL."""
    intake_url = get_intake_url(session)
    if not intake_url:
        return None
    return generate_qr_payload(intake_url)


def get_raw_token(session: RaterSession) -> Optional[str]:
    """Recover the raw token by decrypting the stored encrypted copy."""
    if not session.encrypted_token:
        return None
    try:
        return decrypt_value(session.encrypted_token)
    except Exception:
        return None


def get_session_by_id(session_id: uuid.UUID, db: Session) -> Optional[RaterSession]:
    return db.get(RaterSession, session_id)


def regenerate_session_token(
    session: RaterSession,
    db: Session,
) -> dict:
    """Revoke the current token and issue a fresh one for the same rater.

    Only allowed while the session hasn't been submitted. Returns the raw
    token + intake URL + QR payload so the counselor can share the new link.
    """
    if session.status == SessionStatus.SUBMITTED:
        raise ValueError("Cannot regenerate a submitted session.")

    raw_token = _generate_token()
    token_hash = _hash_token(raw_token)
    intake_url = build_intake_url(raw_token)

    session.token_hash = token_hash
    session.encrypted_token = encrypt_value(raw_token)
    session.encrypted_intake_url = encrypt_value(intake_url)
    # Re-arm the session if it had expired; keep it unlocked for resend.
    if session.status == SessionStatus.EXPIRED:
        session.status = SessionStatus.CREATED
        session.started_at = None
    session.expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.intake_token_ttl_hours
    )
    db.add(session)

    audit = AuditEvent(
        case_id=session.case_id,
        actor_type=ActorType.SYSTEM,
        actor_id=session.id,
        event_type="RATER_LINK_REGENERATED",
        event_metadata={"rater_type": session.rater_type.value},
    )
    db.add(audit)
    db.commit()
    db.refresh(session)

    return {
        "session_id": str(session.id),
        "rater_type": session.rater_type.value,
        "token": raw_token,
        "intake_url": intake_url,
        "qr_payload": generate_qr_payload(intake_url),
    }


def get_session_by_token(token: str, db: Session) -> Optional[RaterSession]:
    token_hash = _hash_token(token)
    session = db.exec(
        select(RaterSession).where(RaterSession.token_hash == token_hash)
    ).first()
    if not session:
        return None
    if session.status == SessionStatus.CREATED:
        session.status = SessionStatus.STARTED
        session.started_at = datetime.now(timezone.utc)
        db.add(session)

        audit = AuditEvent(
            case_id=session.case_id,
            actor_type=ActorType.RATER,
            actor_id=session.id,
            event_type="RATER_INTAKE_STARTED",
            event_metadata={"rater_type": session.rater_type.value},
        )
        db.add(audit)
        db.commit()
        db.refresh(session)
    return session


def get_questionnaire(token: str, db: Session) -> dict:
    """Return only the questionnaire for this rater — never other raters' data."""
    session = get_session_by_token(token, db)
    if not session:
        raise ValueError("Invalid or expired intake token.")
    if session.status in (
        SessionStatus.SUBMITTED,
        SessionStatus.EXPIRED,
        SessionStatus.REVOKED,
    ):
        raise ValueError(f"Session is {session.status.value}.")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        session.status = SessionStatus.EXPIRED
        db.add(session)
        db.commit()
        raise ValueError("Intake token has expired.")

    questions = db.exec(
        select(Question)
        .where(Question.active == True)
        .order_by(Question.display_order)
    ).all()

    responses = db.exec(
        select(Response).where(Response.session_id == session.id)
    ).all()
    saved = {str(r.question_id): r.value for r in responses}

    return {
        "session_id": str(session.id),
        "rater_type": session.rater_type.value,
        "expires_at": session.expires_at.isoformat(),
        "status": session.status.value,
        "questions": [
            {
                "id": str(q.id),
                "code": q.question_code,
                "text": q.question_text,
                "response_type": q.response_type.value,
                "validation": q.validation_config,
                "required": q.required,
                "order": q.display_order,
                "saved_value": saved.get(str(q.id)),
            }
            for q in questions
        ],
    }


def save_response(
    token: str,
    question_id: uuid.UUID,
    value: any,
    db: Session,
) -> Response:
    session = get_session_by_token(token, db)
    if not session or session.status == SessionStatus.SUBMITTED:
        raise ValueError("Cannot save response: session is locked or invalid.")

    question = db.get(Question, question_id)
    if not question:
        raise ValueError("Question not found.")

    _validate_response_value(question, value)

    existing = db.exec(
        select(Response).where(
            Response.session_id == session.id,
            Response.question_id == question_id,
        )
    ).first()

    if existing:
        existing.value = value
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        db.commit()
        return existing
    else:
        response = Response(
            session_id=session.id,
            question_id=question_id,
            value=value,
        )
        db.add(response)
        db.commit()
        return response


def submit_session(token: str, db: Session) -> dict:
    """Lock session, create audit event."""
    session = get_session_by_token(token, db)
    if not session:
        raise ValueError("Invalid token.")
    if session.status == SessionStatus.SUBMITTED:
        return {"status": "already_submitted"}

    questions = db.exec(
        select(Question).where(Question.active == True, Question.required == True)
    ).all()
    responses = db.exec(
        select(Response).where(Response.session_id == session.id)
    ).all()
    answered_ids = {str(r.question_id) for r in responses}
    missing = [
        q.question_code for q in questions if str(q.id) not in answered_ids
    ]
    if missing:
        raise ValueError(f"Required questions not answered: {missing}")

    session.status = SessionStatus.SUBMITTED
    session.submitted_at = datetime.now(timezone.utc)
    db.add(session)

    audit = AuditEvent(
        case_id=session.case_id,
        actor_type=ActorType.RATER,
        actor_id=session.id,
        event_type="QUESTIONNAIRE_SUBMITTED",
        event_metadata={"rater_type": session.rater_type.value},
    )
    db.add(audit)
    db.commit()

    return {"status": "submitted", "rater_type": session.rater_type.value}


def _validate_response_value(question: Question, value: any) -> None:
    cfg = question.validation_config or {}
    if question.response_type.value == "LIKERT":
        min_val = cfg.get("min", 1)
        max_val = cfg.get("max", 5)
        if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
            raise ValueError(
                f"Likert value must be between {min_val} and {max_val}."
            )
    elif question.response_type.value == "INTEGER":
        if not isinstance(value, int):
            raise ValueError("Value must be an integer.")
    elif question.response_type.value == "BOOLEAN":
        if not isinstance(value, bool):
            raise ValueError("Value must be a boolean.")
