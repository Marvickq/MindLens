import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class SignalLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEANINGFUL = "MEANINGFUL"


class DiscrepancyStatus(str, Enum):
    VALIDATED = "validated"
    UNVALIDATED = "unvalidated"


class DiscrepancyMethodology(str, Enum):
    """
    Supported discrepancy comparison methodologies.

    A methodology only yields a validated result when its required research
    parameters are explicitly configured. SED is a candidate methodology —
    it must never be assumed automatically validated.
    """
    SED = "sed"


class DiscrepancyMethodConfig(SQLModel, table=True):
    """
    Research-derived configuration that drives the discrepancy engine.

    Parameters are loaded from a validated research instrument/study. Nothing
    here is a hardcoded fallback: if a row is missing (or incomplete/inactive),
    the engine marks the resulting discrepancy `unvalidated` and does NOT emit
    a "meaningful divergence" verdict.

    interpretation_model is always the operations triad for this application.
    """
    __tablename__ = "discrepancy_method_configs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    instrument_version: str = Field(max_length=50)
    dimension_id: uuid.UUID = Field(foreign_key="dimensions.id")

    # Rater pair — one of PARENT_TEACHER / PARENT_ADOLESCENT / TEACHER_ADOLESCENT
    rater_pair: str = Field(max_length=50)

    methodology: DiscrepancyMethodology = Field(default=DiscrepancyMethodology.SED)
    calculation_method: str = Field(max_length=100)
    calculation_version: str = Field(max_length=50)

    # Required for SED methodology (never defaulted, never fabricated)
    reliability: Optional[float] = None
    reliability_source: Optional[str] = None
    reference_sd: Optional[float] = None
    reference_sd_source: Optional[str] = None

    # Optional research-derived significance criterion for the method, if the
    # methodology defines one. When absent the method must define its own
    # evidence-based comparison.
    significance_threshold: Optional[float] = None

    source_citation: Optional[str] = None
    interpretation_model: str = Field(default="operations_triad", max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Discrepancy(SQLModel, table=True):
    __tablename__ = "discrepancies"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    dimension_id: uuid.UUID = Field(foreign_key="dimensions.id")
    rater_a: str  # RaterType — alphabetically smaller of the pair
    rater_b: str  # RaterType — alphabetically larger of the pair
    score_a: float
    score_b: float
    divergence: float
    signal_level: SignalLevel = Field(default=SignalLevel.NONE)
    calculation_method: str = Field(max_length=100)
    calculation_version: str = Field(max_length=50)
    reference_sed: Optional[float] = None

    # Research-config provenance (retained per record)
    interpretation_model: str = Field(default="operations_triad", max_length=50)
    instrument_version: Optional[str] = Field(default=None, max_length=50)
    rater_pair: Optional[str] = Field(default=None, max_length=50)  # e.g. PARENT_TEACHER
    reliability_source: Optional[str] = None
    reference_source: Optional[str] = None
    status: str = Field(default="unvalidated", max_length=20)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Signal(SQLModel, table=True):
    __tablename__ = "signals"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    case_id: uuid.UUID = Field(foreign_key="student_cases.id")
    discrepancy_id: uuid.UUID = Field(foreign_key="discrepancies.id", nullable=True, default=None)
    dimension_id: uuid.UUID = Field(foreign_key="dimensions.id")
    title: str = Field(max_length=500)
    description: str
    signal_level: SignalLevel

    # Research-config provenance (retained per signal record)
    interpretation_model: str = Field(default="operations_triad", max_length=50)
    instrument_version: Optional[str] = Field(default=None, max_length=50)
    rater_pair: Optional[str] = Field(default=None, max_length=50)
    status: str = Field(default="unvalidated", max_length=20)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
