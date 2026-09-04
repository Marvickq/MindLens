"""
Evidence Service
Returns the complete evidence chain for a signal.
Chain: Rater → Question → Response → Dimension → Score → Dyad → Discrepancy → Evidence
Powers the "Why was this flagged?" drawer in the UI.
"""
import uuid

from sqlmodel import Session, select
from sqlalchemy import text

from app.models.discrepancy import Signal, Discrepancy
from app.models.assessment import Dimension, Question
from app.models.response import Response
from app.models.rater import RaterSession
from app.models.evidence import Evidence
from app.models.dimension_score import DimensionScore
from app.models.audit_event import AuditEvent, ActorType


def get_evidence_chain(case_id: uuid.UUID, signal_id: uuid.UUID, db: Session) -> dict:
    """Full traceable evidence chain for a signal."""
    signal = db.exec(
        select(Signal).where(Signal.id == signal_id, Signal.case_id == case_id)
    ).first()
    if not signal:
        raise ValueError("Signal not found.")

    disc = db.get(Discrepancy, signal.discrepancy_id) if signal.discrepancy_id else None
    dim = db.get(Dimension, signal.dimension_id)

    # Fetch source items — responses from both raters for this dimension
    source_items = []
    if disc:
        for rater_type in [disc.rater_a, disc.rater_b]:
            session = db.exec(
                select(RaterSession).where(
                    RaterSession.case_id == case_id,
                    RaterSession.rater_type == rater_type,
                )
            ).first()
            if not session:
                continue
            questions = db.exec(
                select(Question).where(Question.dimension_id == signal.dimension_id)
            ).all()
            for q in questions:
                resp = db.exec(
                    select(Response).where(
                        Response.session_id == session.id,
                        Response.question_id == q.id,
                    )
                ).first()
                if resp:
                    source_items.append({
                        "question_code": q.question_code,
                        "question_text": q.question_text,
                        "rater": rater_type,
                        "response": resp.value,
                    })

    # Fetch linked evidence records
    ev_rows = db.exec(
        text(
            "SELECT e.* FROM evidence e "
            "JOIN signal_evidence se ON se.evidence_id = e.id "
            "WHERE se.signal_id = :sig_id"
        ),
        {"sig_id": str(signal_id)},
    ).all()

    evidence_list = [
        {
            "evidence_code": row.evidence_code,
            "title": row.title,
            "source": row.source,
            "certainty": row.evidence_certainty,
            "association_value": row.association_value,
            "limitation": row.limitation,
            "citation": row.citation,
        }
        for row in ev_rows
    ]

    # Audit evidence view
    audit = AuditEvent(
        case_id=case_id,
        actor_type=ActorType.COUNSELOR,
        event_type="EVIDENCE_VIEWED",
        event_metadata={"signal_id": str(signal_id)},
    )
    db.add(audit)
    db.commit()

    return {
        "signal": {
            "id": str(signal.id),
            "title": signal.title,
            "description": signal.description,
            "signal_level": signal.signal_level.value,
        },
        "rater_pair": [disc.rater_a, disc.rater_b] if disc else [],
        "dimension": dim.label if dim else None,
        "scores": {
            disc.rater_a: disc.score_a,
            disc.rater_b: disc.score_b,
        } if disc else {},
        "divergence": disc.divergence if disc else None,
        "calculation": {
            "method": disc.calculation_method,
            "version": disc.calculation_version,
        } if disc else {},
        "source_items": source_items,
        "evidence": evidence_list,
    }
