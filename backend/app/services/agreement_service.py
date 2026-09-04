"""
Agreement Service — Discrepancy Engine (research configuration-driven)

Compares rater pairs across all six dimensions.
Supported rater pairs are kept DISTINCT:
    PARENT↔TEACHER, PARENT↔ADOLESCENT, TEACHER↔ADOLESCENT

Design rules:
  * No hardcoded divergence thresholds, reliability coefficients, SDs, or
    "meaningful" cutoffs. Every research parameter comes from the
    `discrepancy_method_configs` table (loaded from a validated instrument).
  * never use fallback/default reliability, SD, or threshold values.
  * If the required research configuration for (instrument, dimension,
    rater pair) is MISSING/inactive/incomplete, the discrepancy is recorded
    with status = "unvalidated" and NO "meaningful divergence" verdict is
    emitted (signal_level stays NONE, no signal is generated).
  * SED is a supported CANDIDATE methodology only:
        SEM = SD × sqrt(1 - reliability)
        SED = sqrt(SEM_a² + SEM_b²)
    It produces a validated result only when methodology + parameters are
    explicitly configured. We never assume it is validated by default.
"""
import math
import uuid

from sqlmodel import Session, select

from app.models.dimension_score import DimensionScore
from app.models.discrepancy import (
    Discrepancy,
    DiscrepancyMethodConfig,
    DiscrepancyMethodology,
    DiscrepancyStatus,
    SignalLevel,
)
from app.models.assessment import Dimension
from app.models.audit_event import AuditEvent, ActorType

CONFIGURED_METHOD = "configured_discrepancy_engine_v1"
CONFIGURED_VERSION = "1.0"
INSTRUMENT_VERSION = "1.0"


def _rater_pair_key(rater_a: str, rater_b: str) -> str:
    """Canonical rater pair key, e.g. 'PARENT_TEACHER'."""
    return f"{rater_a}_{rater_b}"


def _load_config(
    db: Session,
    dimension_id: uuid.UUID,
    rater_pair: str,
) -> DiscrepancyMethodConfig | None:
    return db.exec(
        select(DiscrepancyMethodConfig).where(
            DiscrepancyMethodConfig.is_active == True,
            DiscrepancyMethodConfig.dimension_id == dimension_id,
            DiscrepancyMethodConfig.rater_pair == rater_pair,
            DiscrepancyMethodConfig.instrument_version == INSTRUMENT_VERSION,
        )
    ).first()


def _sed_is_complete(cfg: DiscrepancyMethodConfig) -> bool:
    """
    SED is complete only when the required research parameters are present.
    No fallback values are ever used.
    """
    return (
        cfg.reliability is not None
        and cfg.reference_sd is not None
        and bool(cfg.reliability_source)
    )


def _apply_methodology(cfg: DiscrepancyMethodConfig):
    """
    Compute the configured methodology reference (SED) for the pair.
    Returns (reference_sed, significance_threshold).
    Both raters use the same instrument/version in this configuration.
    """
    reference_sed = None
    significance_threshold = cfg.significance_threshold
    if cfg.methodology == DiscrepancyMethodology.SED and cfg.reliability is not None:
        # SEM = SD × sqrt(1 - reliability)
        sem = cfg.reference_sd * math.sqrt(1.0 - cfg.reliability)
        # SED = sqrt(SEM_a² + SEM_b²); both raters share the instrument SEM here
        reference_sed = math.sqrt(sem * sem + sem * sem)
    return reference_sed, significance_threshold


def _verdict(divergence: float, significance_threshold, status) -> SignalLevel:
    if status != DiscrepancyStatus.VALIDATED:
        return SignalLevel.NONE
    if significance_threshold is None:
        # Validated comparison, but no explicit significance criterion
        # configured for this method → no "meaningful divergence" claim.
        return SignalLevel.NONE
    if divergence >= significance_threshold:
        return SignalLevel.MEANINGFUL
    return SignalLevel.NONE


def calculate_discrepancies(case_id: uuid.UUID, db: Session) -> list[Discrepancy]:
    """
    For each available rater pair × each dimension, compute and store the
    observed divergence plus the research-config-driven verdict.
    Handles missing-rater gracefully — skips pairs where data is unavailable.
    """
    dimensions = db.exec(select(Dimension).where(Dimension.active == True)).all()
    scores_rows = db.exec(
        select(DimensionScore).where(DimensionScore.case_id == case_id)
    ).all()

    # Group: {rater_type: {dimension_id: score}}
    score_map: dict[str, dict[str, float]] = {}
    for row in scores_rows:
        score_map.setdefault(row.rater_type, {})[str(row.dimension_id)] = row.score

    available_raters = sorted(score_map.keys())
    dyads = [
        (available_raters[i], available_raters[j])
        for i in range(len(available_raters))
        for j in range(i + 1, len(available_raters))
    ]

    results = []
    for rater_a, rater_b in dyads:
        pair_key = _rater_pair_key(rater_a, rater_b)
        for dim in dimensions:
            dim_id = str(dim.id)
            score_a = score_map.get(rater_a, {}).get(dim_id)
            score_b = score_map.get(rater_b, {}).get(dim_id)
            if score_a is None or score_b is None:
                continue  # Missing rater — skip gracefully

            # Observed absolute difference between the two perspectives.
            divergence = round(abs(score_a - score_b), 6)

            cfg = _load_config(db, dim.id, pair_key)
            validated = bool(cfg) and _sed_is_complete(cfg)
            if cfg and validated:
                status = DiscrepancyStatus.VALIDATED
                reference_sed, threshold = _apply_methodology(cfg)
                instrument_version = cfg.instrument_version
                reliability_source = cfg.reliability_source
                reference_source = cfg.source_citation or cfg.reference_sd_source
                interpretation_model = cfg.interpretation_model or "operations_triad"
                calculation_method = cfg.calculation_method or CONFIGURED_METHOD
                calculation_version = cfg.calculation_version or CONFIGURED_VERSION
            else:
                status = DiscrepancyStatus.UNVALIDATED
                reference_sed = None
                threshold = None
                instrument_version = INSTRUMENT_VERSION
                reliability_source = None
                reference_source = None
                interpretation_model = "operations_triad"
                calculation_method = CONFIGURED_METHOD
                calculation_version = CONFIGURED_VERSION

            level = _verdict(divergence, threshold, status)

            # Upsert
            existing = db.exec(
                select(Discrepancy).where(
                    Discrepancy.case_id == case_id,
                    Discrepancy.dimension_id == dim.id,
                    Discrepancy.rater_a == rater_a,
                    Discrepancy.rater_b == rater_b,
                )
            ).first()

            provenance = dict(
                interpretation_model=interpretation_model,
                instrument_version=instrument_version,
                rater_pair=pair_key,
                reliability_source=reliability_source,
                reference_source=reference_source,
                status=status,
            )

            if existing:
                existing.score_a = score_a
                existing.score_b = score_b
                existing.divergence = divergence
                existing.signal_level = level
                existing.reference_sed = reference_sed
                existing.calculation_method = calculation_method
                existing.calculation_version = calculation_version
                for k, v in provenance.items():
                    setattr(existing, k, v)
                db.add(existing)
                results.append(existing)
            else:
                disc = Discrepancy(
                    case_id=case_id,
                    dimension_id=dim.id,
                    rater_a=rater_a,
                    rater_b=rater_b,
                    score_a=score_a,
                    score_b=score_b,
                    divergence=divergence,
                    signal_level=level,
                    reference_sed=reference_sed,
                    calculation_method=calculation_method,
                    calculation_version=calculation_version,
                    **provenance,
                )
                db.add(disc)
                results.append(disc)

    audit = AuditEvent(
        case_id=case_id,
        actor_type=ActorType.SYSTEM,
        event_type="DISCREPANCY_CALCULATED",
        event_metadata={
            "calculation_version": CONFIGURED_VERSION,
            "dyads": len(dyads),
            "engine": "research_configuration_driven",
        },
    )
    db.add(audit)
    db.commit()
    return results
