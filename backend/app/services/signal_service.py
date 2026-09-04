"""
Signal Service
Converts VALIDATED discrepancies into neutral, human-readable dashboard signals.

Signals describe DIFFERENCES between perspectives under a configured
comparison method. They do NOT diagnose the student, imply severity, risk,
or state which rater is "correct".

Wording stays neutral, e.g.:
    "Parent and Teacher reports on Adaptability differ under the configured
     comparison method."

Only discrepancies with status="validated" AND signal_level != NONE generate
a signal. An unvalidated discrepancy never produces a signal.
"""
import uuid

from sqlalchemy import text
from sqlmodel import Session, select

from app.models.discrepancy import (
    Discrepancy,
    DiscrepancyStatus,
    Signal,
    SignalLevel,
)
from app.models.assessment import Dimension
from app.models.evidence import Evidence


RATER_DISPLAY = {
    "PARENT": "Parent",
    "TEACHER": "Teacher",
    "ADOLESCENT": "Adolescent",
}


def _rater_pair_display(rater_pair: str) -> str:
    parts = rater_pair.split("_", 1)
    if len(parts) == 2:
        return f"{RATER_DISPLAY.get(parts[0], parts[0])} and {RATER_DISPLAY.get(parts[1], parts[1])}"
    return rater_pair


def generate_signals(case_id: uuid.UUID, db: Session) -> list[Signal]:
    """
    Generate a neutral signal for each validated discrepancy that meets the
    configured significance criterion. Regenerates (deletes) prior signals
    for the case, consistent with the previous engine behaviour.
    """
    validated_discs = db.exec(
        select(Discrepancy).where(
            Discrepancy.case_id == case_id,
            Discrepancy.status == DiscrepancyStatus.VALIDATED,
            Discrepancy.signal_level != SignalLevel.NONE,
        )
    ).all()

    # Delete old signals for this case before regenerating. signal_evidence
    # rows must be removed first (FK to signals is RESTRICT on the live DB).
    old_signals = db.exec(
        select(Signal).where(Signal.case_id == case_id)
    ).all()
    for s in old_signals:
        db.exec(
            text("DELETE FROM signal_evidence WHERE signal_id = :sid"),
            params={"sid": str(s.id)},
        )
        db.delete(s)

    created = []
    for disc in validated_discs:
        dim = db.get(Dimension, disc.dimension_id)
        dim_label = dim.label if dim else "Unknown Dimension"
        pair_label = _rater_pair_display(disc.rater_pair or "PARENT_TEACHER")

        title = (
            f"{pair_label} reports on {dim_label} differ under the configured "
            f"comparison method"
        )
        description = (
            f"Under the configured comparison method (calculation "
            f"{disc.calculation_method} v{disc.calculation_version}, "
            f"instrument v{disc.instrument_version or 'n/a'}), the observed "
            f"divergence between {RATER_DISPLAY.get(disc.rater_a, disc.rater_a)} "
            f"({disc.score_a:.0f}/100) and "
            f"{RATER_DISPLAY.get(disc.rater_b, disc.rater_b)} "
            f"({disc.score_b:.0f}/100) on {dim_label} is {disc.divergence:.1f} points. "
            f"This is reported as a difference between perspectives; it does not "
            f"imply which report is correct."
        )

        signal = Signal(
            case_id=case_id,
            discrepancy_id=disc.id,
            dimension_id=disc.dimension_id,
            title=title,
            description=description,
            signal_level=disc.signal_level,
            interpretation_model=disc.interpretation_model or "operations_triad",
            instrument_version=disc.instrument_version,
            rater_pair=disc.rater_pair,
            status=disc.status,
        )
        db.add(signal)
        db.flush()  # get signal.id before commit

        # Link to evidence if available
        evidence_records = db.exec(select(Evidence).limit(1)).all()
        if evidence_records:
            db.exec(
                text(
                    "INSERT INTO signal_evidence (signal_id, evidence_id) "
                    "VALUES (:sig, :ev) ON CONFLICT DO NOTHING"
                ),
                params={"sig": str(signal.id), "ev": str(evidence_records[0].id)},
            )

        created.append(signal)

    db.commit()
    return created


def reconcile_signal_state(db: Session) -> int:
    """
    Reconcile stored discrepancy/signal state after an engine or schema change.

    Any discrepancy NOT validated under the CURRENT configured comparison
    method must not carry a meaningful-divergence level, and signals are
    regenerated from the current validated state. This removes stale signals
    (and misleading levels) emitted by earlier hardcoded-threshold engines,
    while keeping the validated, config-driven ones. It is idempotent.
    """
    discs = db.exec(
        select(Discrepancy).where(
            Discrepancy.status != DiscrepancyStatus.VALIDATED,
            Discrepancy.signal_level != SignalLevel.NONE,
        )
    ).all()
    for d in discs:
        d.signal_level = SignalLevel.NONE
        db.add(d)
    db.commit()

    cases_rows = db.exec(select(Discrepancy.case_id)).all()
    cases = set()
    for row in cases_rows:
        case_id = row[0] if isinstance(row, (list, tuple)) else row
        cases.add(case_id)
    for case_id in cases:
        generate_signals(case_id, db)
    return len(cases)
