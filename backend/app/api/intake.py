"""
Intake API — Public-facing rater questionnaire endpoints.
No JWT auth required; token-based authorization only.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.schemas.schemas import IntakeResponseSubmit
from app.services import (
    intake_service, scoring_service, agreement_service, signal_service,
)
from app.models.rater import RaterSession, SessionStatus
from app.models.case import StudentCase, CaseStatus
from app.models.audit_event import AuditEvent, ActorType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])


@router.get("/{token}")
def get_intake_questionnaire(token: str, db: Session = Depends(get_session)):
    try:
        return intake_service.get_questionnaire(token, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{token}/responses")
def save_intake_response(
    token: str,
    payload: IntakeResponseSubmit,
    db: Session = Depends(get_session),
):
    try:
        resp = intake_service.save_response(
            token=token,
            question_id=payload.question_id,
            value=payload.value,
            db=db,
        )
        return {"status": "saved", "response_id": str(resp.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{token}/responses")
def patch_intake_response(
    token: str,
    payload: IntakeResponseSubmit,
    db: Session = Depends(get_session),
):
    try:
        resp = intake_service.save_response(
            token=token,
            question_id=payload.question_id,
            value=payload.value,
            db=db,
        )
        return {"status": "saved", "response_id": str(resp.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{token}/submit")
def submit_intake(token: str, db: Session = Depends(get_session)):
    try:
        res = intake_service.submit_session(token, db)

        session = intake_service.get_session_by_token(token, db)
        if session:
            case_id = session.case_id
            all_sessions = db.exec(
                select(RaterSession).where(RaterSession.case_id == case_id)
            ).all()

            all_done = all(
                s.status == SessionStatus.SUBMITTED for s in all_sessions
            )
            if all_done:
                logger.info(f"All sessions submitted for case {case_id}, triggering scoring pipeline.")
                scoring_service.calculate_all_scores(case_id, db)
                agreement_service.calculate_discrepancies(case_id, db)
                signal_service.generate_signals(case_id, db)

                case = db.get(StudentCase, case_id)
                if case:
                    case.status = CaseStatus.READY_FOR_REVIEW
                    db.add(case)
                    db.commit()
            else:
                submitted_count = sum(
                    1 for s in all_sessions if s.status == SessionStatus.SUBMITTED
                )
                total = len(all_sessions)
                logger.info(
                    f"Session submitted for case {case_id}. "
                    f"Progress: {submitted_count}/{total}"
                )

        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
