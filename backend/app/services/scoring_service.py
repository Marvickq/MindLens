"""
Scoring Service
Deterministic, versioned dimension score calculation.
NO LLM. NO hidden weights.
The exact aggregation must follow the selected research instrument.
"""
import uuid
from typing import List

from sqlmodel import Session, select

from app.models.response import Response
from app.models.assessment import Question, Dimension
from app.models.dimension_score import DimensionScore
from app.models.rater import RaterSession, SessionStatus, RaterType
from app.models.audit_event import AuditEvent, ActorType

CALCULATION_METHOD = "mean_normalization_v1"
CALCULATION_VERSION = "1.0"
QUESTIONNAIRE_VERSION = "1.0"

# Placeholder: scores normalized to 0–100 scale.
# IMPORTANT: Replace this method with the exact scoring formula
# from the validated research instrument used in the project.


def calculate_dimension_score(
    responses: list[dict],  # [{"value": int, "dimension_id": str}]
    dimension_id: uuid.UUID,
) -> float:
    """
    Aggregate responses for a single dimension.
    Placeholder: mean of Likert values, normalized to 0–100.
    Replace with research-instrument formula.
    """
    dim_values = [
        r["value"] for r in responses
        if str(r["dimension_id"]) == str(dimension_id)
        and isinstance(r["value"], (int, float))
    ]
    if not dim_values:
        return 0.0
    raw_mean = sum(dim_values) / len(dim_values)
    # Normalize assuming Likert 1–5 → 0–100
    normalized = ((raw_mean - 1) / 4) * 100
    return round(normalized, 4)


def calculate_all_scores(case_id: uuid.UUID, db: Session) -> list[DimensionScore]:
    """
    Calculate dimension scores for all submitted rater sessions in this case.
    Idempotent: overwrites existing scores for the same case/rater/dimension.
    """
    dimensions = db.exec(select(Dimension).where(Dimension.active == True)).all()
    sessions = db.exec(
        select(RaterSession).where(
            RaterSession.case_id == case_id,
            RaterSession.status == SessionStatus.SUBMITTED,
        )
    ).all()

    scores_created = []

    for session in sessions:
        # Fetch responses with their question's dimension
        stmt = (
            select(Response, Question)
            .join(Question, Response.question_id == Question.id)
            .where(Response.session_id == session.id)
        )
        rows = db.exec(stmt).all()
        response_data = [
            {"value": r.value, "dimension_id": q.dimension_id}
            for r, q in rows
        ]

        for dim in dimensions:
            score_val = calculate_dimension_score(response_data, dim.id)

            # Upsert
            existing = db.exec(
                select(DimensionScore).where(
                    DimensionScore.case_id == case_id,
                    DimensionScore.rater_type == session.rater_type.value,
                    DimensionScore.dimension_id == dim.id,
                )
            ).first()

            if existing:
                existing.score = score_val
                db.add(existing)
            else:
                ds = DimensionScore(
                    case_id=case_id,
                    rater_type=session.rater_type.value,
                    dimension_id=dim.id,
                    score=score_val,
                    questionnaire_version=QUESTIONNAIRE_VERSION,
                    calculation_method=CALCULATION_METHOD,
                    calculation_version=CALCULATION_VERSION,
                )
                db.add(ds)
                scores_created.append(ds)

    # Audit
    audit = AuditEvent(
        case_id=case_id,
        actor_type=ActorType.SYSTEM,
        event_type="SCORES_CALCULATED",
        event_metadata={"calculation_version": CALCULATION_VERSION},
    )
    db.add(audit)
    db.commit()
    return scores_created
