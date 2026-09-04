"""
Cases API — Counselor-facing case management.
All routes require JWT authentication.
"""
import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.case import StudentCase, CaseStatus
from app.models.rater import RaterSession, SessionStatus
from app.models.dimension_score import DimensionScore
from app.models.discrepancy import Discrepancy, Signal
from app.models.assessment import Dimension
from app.models.audit_event import AuditEvent, ActorType
from app.models.counselor import User
from app.schemas.schemas import (
    CaseCreate, CaseSummary, CaseDetail, CaseSessionInfo,
    DashboardSummary, ReviewSubmit, CaseCreationResponse,
    IntakeSessionInfo, HeatmapCell, HeatmapResponse,
    PresentedAuditTrail,
)
from app.services import (
    intake_service, scoring_service, agreement_service,
    signal_service, evidence_service, review_service,
    report_service, audit_service, audit_presentation,
    ai_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["counselor"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    cases = db.exec(
        select(StudentCase).where(StudentCase.organization_id == user.organization_id)
    ).all()
    summary = {
        "awaiting_responses": 0,
        "ready_for_review": 0,
        "under_review": 0,
        "completed": 0,
    }
    for c in cases:
        key = c.status.value.lower()
        if key in summary:
            summary[key] += 1
    return DashboardSummary(**summary)


@router.get("/cases", response_model=List[CaseSummary])
def list_cases(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(StudentCase).where(
        StudentCase.organization_id == user.organization_id
    ).order_by(StudentCase.created_at.desc())
    if status:
        query = query.where(StudentCase.status == status)
    if search:
        query = query.where(StudentCase.display_name.contains(search))
    return db.exec(query).all()


@router.post("/cases", response_model=CaseCreationResponse)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    logger.info(f"Creating case: {payload.display_name} by user {user.id}")
    case = StudentCase(
        organization_id=user.organization_id,
        display_name=payload.display_name,
        grade=payload.grade,
        school=payload.school,
        external_reference=payload.external_reference,
        status=CaseStatus.WAITING_FOR_RESPONSES,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    intakes = intake_service.create_intake_sessions(
        case.id, db
    )

    audit_service.create_audit_event(
        case_id=case.id,
        actor_type=ActorType.COUNSELOR,
        actor_id=user.id,
        event_type="CASE_CREATED",
        metadata={"display_name": payload.display_name},
        db=db,
    )
    db.commit()

    sessions = [
        IntakeSessionInfo(
            rater_type=i["rater_type"],
            status="PENDING",
            token=i["token"],
            intake_url=i["intake_url"],
            qr_payload=i["qr_payload"],
        )
        for i in intakes
    ]

    return CaseCreationResponse(
        case_id=case.id,
        display_name=case.display_name,
        status=case.status.value,
        grade=case.grade,
        school=case.school,
        sessions=sessions,
    )


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_detail(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    sessions = db.exec(
        select(RaterSession).where(RaterSession.case_id == case_id)
    ).all()

    review = review_service.get_counselor_review(case_id, db)

    sessions_out = [
        CaseSessionInfo(
            rater_type=s.rater_type.value,
            status=intake_service.status_label(s),
            submitted_at=s.submitted_at,
        )
        for s in sessions
    ]

    return CaseDetail(
        id=case.id,
        display_name=case.display_name,
        external_reference=case.external_reference,
        grade=case.grade,
        school=case.school,
        status=case.status.value,
        created_at=case.created_at,
        updated_at=case.updated_at,
        sessions=sessions_out,
        review=review,
    )


@router.get("/cases/{case_id}/sessions")
def get_case_sessions(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    sessions = db.exec(
        select(RaterSession).where(RaterSession.case_id == case_id)
    ).all()

    result = []
    for s in sessions:
        session_info = intake_service.build_session_info(s)
        intake_url = session_info["intake_url"]
        result.append({
            "session_id": session_info["id"],
            "rater_type": session_info["rater_type"],
            "status": session_info["status"],
            "submitted_at": session_info["submitted_at"],
            "expires_at": session_info["expires_at"],
            "intake_url": intake_url,
            "qr_payload": intake_service.generate_qr_for_session(s) if intake_url else None,
        })

    return result


@router.get("/cases/{case_id}/sessions/{session_id}/qr")
def get_case_session_qr(
    case_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    session = intake_service.get_session_by_id(session_id, db)
    if not session or session.case_id != case_id:
        raise HTTPException(status_code=404, detail="Session not found")

    intake_url = intake_service.get_intake_url(session)
    if not intake_url:
        raise HTTPException(status_code=409, detail="Intake link unavailable")

    qr_payload = intake_service.generate_qr_for_session(session)
    audit_service.create_audit_event(
        case_id=case_id,
        actor_type=ActorType.COUNSELOR,
        actor_id=user.id,
        event_type="RATER_QR_GENERATED",
        metadata={"rater_type": session.rater_type.value},
        db=db,
    )
    db.commit()

    return qr_payload


@router.post("/cases/{case_id}/sessions/{session_id}/regenerate")
def regenerate_session(
    case_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    session = intake_service.get_session_by_id(session_id, db)
    if not session or session.case_id != case_id:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        regenerated = intake_service.regenerate_session_token(session, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    audit_service.create_audit_event(
        case_id=case_id,
        actor_type=ActorType.COUNSELOR,
        actor_id=user.id,
        event_type="RATER_LINK_REGENERATED",
        metadata={"rater_type": session.rater_type.value},
        db=db,
    )
    db.commit()
    return regenerated


@router.post("/cases/{case_id}/sessions")
def regenerate_sessions(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    intakes = intake_service.create_intake_sessions(
        case.id, db
    )

    return {
        "sessions": [
            {
                "session_id": i["session_id"],
                "rater_type": i["rater_type"],
                "token": i["token"],
                "intake_url": i["intake_url"],
                "qr_payload": i["qr_payload"],
            }
            for i in intakes
        ]
    }


@router.get("/cases/{case_id}/heatmap")
def get_case_heatmap(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    dimensions = db.exec(
        select(Dimension).where(Dimension.active == True).order_by(Dimension.display_order)
    ).all()

    scores = db.exec(
        select(DimensionScore).where(DimensionScore.case_id == case_id)
    ).all()

    score_map = {}
    for s in scores:
        key = (str(s.dimension_id), s.rater_type)
        score_map[key] = s.score

    raters = ["PARENT", "TEACHER", "ADOLESCENT"]
    cells = []
    for dim in dimensions:
        for rater in raters:
            score = score_map.get((str(dim.id), rater))
            cells.append(HeatmapCell(
                dimension_id=str(dim.id),
                dimension_label=dim.label,
                dimension_code=dim.dimension_code,
                rater_type=rater,
                score=score,
                has_response=score is not None,
            ))

    return HeatmapResponse(
        dimensions=[
            {"id": str(d.id), "label": d.label, "code": d.dimension_code}
            for d in dimensions
        ],
        raters=raters,
        cells=cells,
    )


@router.get("/cases/{case_id}/discrepancies")
def get_case_discrepancies(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    scores_raw = db.exec(
        select(DimensionScore).where(DimensionScore.case_id == case_id)
    ).all()
    discrepancies = db.exec(
        select(Discrepancy).where(Discrepancy.case_id == case_id)
    ).all()

    dim_map = {
        str(d.id): {"label": d.label, "code": d.dimension_code}
        for d in db.exec(select(Dimension)).all()
    }

    scores = [
        {
            "dimension_id": str(s.dimension_id),
            "dimension_label": dim_map.get(str(s.dimension_id), {}).get("label", str(s.dimension_id)),
            "rater_type": s.rater_type,
            "score": s.score,
            "calculation_method": s.calculation_method,
            "calculation_version": s.calculation_version,
        }
        for s in scores_raw
    ]

    return {
        "scores": scores,
        "discrepancies": discrepancies,
    }


@router.get("/cases/{case_id}/signals")
def get_case_signals(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    signals = db.exec(
        select(Signal).where(Signal.case_id == case_id)
    ).all()

    dim_map = {
        str(d.id): {"label": d.label, "code": d.dimension_code}
        for d in db.exec(select(Dimension)).all()
    }
    disc_map = {
        str(di.id): di
        for di in db.exec(select(Discrepancy).where(Discrepancy.case_id == case_id)).all()
    }

    result = []
    for sig in signals:
        disc = disc_map.get(str(sig.discrepancy_id)) if sig.discrepancy_id else None
        dim = dim_map.get(str(sig.dimension_id), {})
        scores = {}
        if disc:
            scores[disc.rater_a] = disc.score_a
            scores[disc.rater_b] = disc.score_b
        result.append({
            "id": str(sig.id),
            "case_id": str(sig.case_id),
            "dimension_id": str(sig.dimension_id),
            "discrepancy_id": str(sig.discrepancy_id) if sig.discrepancy_id else None,
            "dimension_label": dim.get("label", "Unknown Dimension"),
            "rater_pair": [disc.rater_a, disc.rater_b] if disc else [],
            "rater_a": disc.rater_a if disc else None,
            "rater_b": disc.rater_b if disc else None,
            "score_a": disc.score_a if disc else None,
            "score_b": disc.score_b if disc else None,
            "divergence": disc.divergence if disc else None,
            "signal_level": sig.signal_level.value,
            "title": sig.title,
            "description": sig.description,
            "created_at": sig.created_at,
        })

    return result


@router.get("/cases/{case_id}/signal-summary")
def get_case_signal_summary(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    dimensions = db.exec(
        select(Dimension).where(Dimension.active == True).order_by(Dimension.display_order)
    ).all()

    score_rows = db.exec(
        select(DimensionScore).where(DimensionScore.case_id == case_id)
    ).all()
    disc_rows = db.exec(
        select(Discrepancy).where(Discrepancy.case_id == case_id)
    ).all()
    signal_rows = db.exec(
        select(Signal).where(Signal.case_id == case_id)
    ).all()

    score_map = {(str(s.dimension_id), s.rater_type): s.score for s in score_rows}
    signal_by_dim: dict[str, Signal] = {}
    for sg in signal_rows:
        signal_by_dim.setdefault(str(sg.dimension_id), sg)

    raters = ["PARENT", "TEACHER", "ADOLESCENT"]

    def _largest_difference(present):
        best = None
        n = len(present)
        for i in range(n):
            for j in range(i + 1, n):
                ra, sa = present[i]
                rb, sb = present[j]
                diff = abs(sa - sb)
                if best is None or diff > best[0]:
                    best = (diff, sorted([ra, rb]))
        return best

    dimensions_payload = []
    for dim in dimensions:
        dim_id = str(dim.id)
        scores = {}
        present = []
        for rater in raters:
            sc = score_map.get((dim_id, rater))
            scores[rater] = sc
            if sc is not None:
                present.append((rater, sc))

        largest = None
        pair = None
        if len(present) >= 2:
            diff, pr = _largest_difference(present)
            if diff is not None:
                largest = round(diff, 1)
                pair = list(pr)

        sg = signal_by_dim.get(dim_id)
        dimensions_payload.append({
            "dimension_id": dim_id,
            "dimension": dim.label,
            "dimension_code": dim.dimension_code,
            "parent_score": scores["PARENT"],
            "teacher_score": scores["TEACHER"],
            "adolescent_score": scores["ADOLESCENT"],
            "largest_difference": largest,
            "largest_difference_pair": pair,
            "signal_id": str(sg.id) if sg else None,
            "signal_level": sg.signal_level.value if sg else "NONE",
            "has_signal": sg is not None,
        })

    return {"dimensions": dimensions_payload}


@router.get("/cases/{case_id}/review")
def get_case_review(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    return review_service.get_counselor_review(case_id, db)


@router.post("/cases/{case_id}/review")
def submit_review(
    case_id: uuid.UUID,
    payload: ReviewSubmit,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        return review_service.create_counselor_review(
            case_id=case_id,
            counselor_id=user.id,
            action=payload.action,
            note=payload.note,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cases/{case_id}/signals/{signal_id}/evidence")
def get_signal_evidence(
    case_id: uuid.UUID,
    signal_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        return evidence_service.get_evidence_chain(case_id, signal_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cases/{case_id}/audit", response_model=PresentedAuditTrail)
def get_case_audit(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    events = audit_service.get_audit_events(case_id, db)
    return audit_presentation.present_audit_trail(events)


@router.post("/cases/{case_id}/report")
def generate_pdf_report(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    audit_service.create_audit_event(
        case_id=case_id,
        actor_type=ActorType.COUNSELOR,
        actor_id=user.id,
        event_type="REPORT_GENERATED",
        metadata={},
        db=db,
    )
    db.commit()

    try:
        pdf_bytes = report_service.generate_case_pdf_report(case_id, db)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=MindLens_report_{case_id}.pdf"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/cases/{case_id}/insights")
def get_ai_insights(
    case_id: uuid.UUID,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    case = db.get(StudentCase, case_id)
    if not case or case.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        return ai_service.get_case_insights(case_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
