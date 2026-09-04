"""
Personalization API — Counselor-led additive question selection.

This supports the counselor's ability to opt additional questions/modules into
a FUTURE session. It never changes the six permanent core dimensions, the
current questionnaire, or the intake/QR workflow. There is no AI selection.

Endpoints are intentionally minimal (backend/data structure only; no UI).
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.counselor import User
from app.models.case import StudentCase
from app.models.personalization import CaseCustomQuestion
from app.models.assessment import Dimension, Question

router = APIRouter(prefix="/api/v1", tags=["personalization"])

# The six permanent core assessment dimensions. Personalization ADDS to these;
# it never replaces, removes, or modifies them.
CORE_DIMENSION_CODES = {
    "attention_persistence",
    "activity",
    "adaptability",
    "sensitivity",
    "sociability",
    "self_regulation",
}


class SelectQuestionRequest(BaseModel):
    question_id: uuid.UUID
    rater_type: Optional[str] = None
    rationale: Optional[str] = None


def _get_owned_case(case_id: uuid.UUID, user: User, db: Session) -> StudentCase:
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases/{case_id}/personalization/questions")
def list_available_questions(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _get_owned_case(case_id, user, db)

    dimensions = db.exec(select(Dimension).order_by(Dimension.display_order)).all()
    dim_map = {str(d.id): d for d in dimensions}
    questions = db.exec(
        select(Question).where(Question.active == True).order_by(Question.display_order)
    ).all()

    selections = db.exec(
        select(CaseCustomQuestion).where(CaseCustomQuestion.case_id == case_id)
    ).all()
    selected_ids = {str(s.question_id) for s in selections}

    return {
        "core_dimensions": [
            {
                "id": str(d.id),
                "code": d.dimension_code,
                "label": d.label,
                "core": d.dimension_code in CORE_DIMENSION_CODES,
            }
            for d in dimensions
        ],
        "questions": [
            {
                "id": str(q.id),
                "question_code": q.question_code,
                "question_text": q.question_text,
                "dimension_id": str(q.dimension_id),
                "dimension": dim_map.get(str(q.dimension_id)).label if dim_map.get(str(q.dimension_id)) else None,
                "core_dimension": (
                    dim_map.get(str(q.dimension_id)).dimension_code in CORE_DIMENSION_CODES
                    if dim_map.get(str(q.dimension_id))
                    else False
                ),
                "selected": q.id in selected_ids,
            }
            for q in questions
        ],
    }


@router.get("/cases/{case_id}/personalization/selections")
def list_selections(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _get_owned_case(case_id, user, db)
    selections = db.exec(
        select(CaseCustomQuestion).where(CaseCustomQuestion.case_id == case_id)
    ).all()
    return [
        {
            "id": str(s.id),
            "question_id": str(s.question_id),
            "rater_type": s.rater_type,
            "rationale": s.rationale,
            "is_enabled": s.is_enabled,
            "created_at": s.created_at,
        }
        for s in selections
    ]


@router.post("/cases/{case_id}/personalization/selections")
def select_question(
    case_id: uuid.UUID,
    payload: SelectQuestionRequest,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _get_owned_case(case_id, user, db)
    q = db.get(Question, payload.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # ADDITIVE only — never duplicates and never overrides a core dimension.
    existing = db.exec(
        select(CaseCustomQuestion).where(
            CaseCustomQuestion.case_id == case_id,
            CaseCustomQuestion.question_id == payload.question_id,
            CaseCustomQuestion.rater_type == payload.rater_type,
        )
    ).first()
    if existing:
        return {
            "id": str(existing.id),
            "question_id": str(existing.question_id),
            "is_enabled": existing.is_enabled,
            "note": "already selected",
        }

    selection = CaseCustomQuestion(
        case_id=case_id,
        question_id=payload.question_id,
        rater_type=payload.rater_type,
        selected_by=user.id,
        rationale=payload.rationale,
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return {
        "id": str(selection.id),
        "question_id": str(selection.question_id),
        "rater_type": selection.rater_type,
        "is_enabled": selection.is_enabled,
    }


@router.delete("/cases/{case_id}/personalization/selections/{selection_id}")
def deselect_question(
    case_id: uuid.UUID,
    selection_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _get_owned_case(case_id, user, db)
    sel = db.exec(
        select(CaseCustomQuestion).where(
            CaseCustomQuestion.id == selection_id,
            CaseCustomQuestion.case_id == case_id,
        )
    ).first()
    if not sel:
        raise HTTPException(status_code=404, detail="Selection not found")
    db.delete(sel)
    db.commit()
    return {"status": "deselected"}
