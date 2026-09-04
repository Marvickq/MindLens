"""
FastAPI Application — MindLens Signal Platform Backend.
"""
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.config import get_settings
from app.database import create_db_and_tables, apply_migrations, engine
from app.api import auth, cases, intake, personalization
from app.models.counselor import Organization, User, UserRole
from app.utils.security import hash_password
from app.models.signal_evidence import SignalEvidence  # noqa: F401
from app.models.discrepancy import DiscrepancyMethodConfig  # noqa: F401
from app.models.personalization import CaseCustomQuestion  # noqa: F401
from app.services.signal_service import reconcile_signal_state

logger = logging.getLogger(__name__)
settings = get_settings()

def seed_organization_if_needed():
    """Ensure a default organization and demo counselor exist."""
    DEV_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    DEV_COUNSELOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

    with Session(engine) as db:
        # Seed Organization
        org = db.get(Organization, DEV_ORG_ID)

        if not org:
            org = Organization(
                id=DEV_ORG_ID,
                name="Greenwood High School",
            )
            db.add(org)
            db.commit()

        # Seed demo counselor
        user = db.get(User, DEV_COUNSELOR_ID)

        if not user:
            user = User(
                id=DEV_COUNSELOR_ID,
                organization_id=DEV_ORG_ID,
                name="Sarah Chen",
                email="sarah.chen@greenwood.edu",
                password_hash=hash_password("MindLens2024!"),
                role=UserRole.COUNSELOR,
                is_active=True,
            )
            db.add(user)
            db.commit()

        logger.info("Default organization and counselor verified.")

def seed_questionnaire_if_needed():
    """Ensure dimensions and basic sample questions exist."""
    with Session(engine) as db:
        ver = db.exec(select(AssessmentVersion)).first()
        if not ver:
            ver = AssessmentVersion(
                name="MindLens Clinical Instrument", version="1.0"
            )
            db.add(ver)
            db.commit()
            db.refresh(ver)

        dimensions = [
            ("attention_persistence", "Attention & Persistence", 1),
            ("activity", "Activity", 2),
            ("adaptability", "Adaptability", 3),
            ("sensitivity", "Sensitivity", 4),
            ("sociability", "Sociability", 5),
            ("self_regulation", "Self-Regulation", 6),
        ]
        dim_map = {}
        for code, label, order in dimensions:
            dim = db.exec(
                select(Dimension).where(Dimension.dimension_code == code)
            ).first()
            if not dim:
                dim = Dimension(
                    dimension_code=code, label=label, display_order=order
                )
                db.add(dim)
                db.commit()
                db.refresh(dim)
            dim_map[code] = dim

        q_count = db.exec(select(Question)).all()
        if not q_count:
            sample_questions = [
                ("attention_persistence", "ILCTI_ATTN_01", "Struggles to maintain focus on quiet or detailed tasks."),
                ("attention_persistence", "ILCTI_ATTN_02", "Easily distracted when working independently."),
                ("attention_persistence", "ILCTI_ATTN_03", "Difficulty following multi-step instructions."),
                ("activity", "ILCTI_ACT_01", "Displays high physical energy or restlessness during structured activities."),
                ("activity", "ILCTI_ACT_02", "Needs frequent movement breaks during schoolwork."),
                ("activity", "ILCTI_ACT_03", "Often fidgets or squirms when expected to sit still."),
                ("adaptability", "ILCTI_ADP_01", "Adapts easily to sudden changes in schedule or routine."),
                ("adaptability", "ILCTI_ADP_02", "Becomes upset when transitioning between activities."),
                ("adaptability", "ILCTI_ADP_03", "Shows flexibility when plans change unexpectedly."),
                ("sensitivity", "ILCTI_SEN_01", "Reacts strongly to mild environmental or social stressors."),
                ("sensitivity", "ILCTI_SEN_02", "Appears deeply affected by criticism or correction."),
                ("sensitivity", "ILCTI_SEN_03", "Responds intensely to loud or chaotic environments."),
                ("sociability", "ILCTI_SOC_01", "Initiates positive social interactions with peers and adults."),
                ("sociability", "ILCTI_SOC_02", "Struggles to read social cues in group settings."),
                ("sociability", "ILCTI_SOC_03", "Prefers solitary activities over group engagement."),
                ("self_regulation", "ILCTI_REG_01", "Manages emotional responses effectively when frustrated."),
                ("self_regulation", "ILCTI_REG_02", "Has difficulty calming down once upset."),
                ("self_regulation", "ILCTI_REG_03", "Responds impulsively before thinking through consequences."),
            ]
            for dim_code, q_code, text in sample_questions:
                q = Question(
                    assessment_version_id=ver.id,
                    dimension_id=dim_map[dim_code].id,
                    question_code=q_code,
                    question_text=text,
                    response_type=ResponseType.LIKERT,
                    display_order=dim_map[dim_code].display_order,
                    validation_config={"min": 1, "max": 5},
                )
                db.add(q)
            db.commit()
            logger.info("Seeded 18 sample questions across 6 dimensions.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    apply_migrations()
    seed_questionnaire_if_needed()
    seed_organization_if_needed()

    with Session(engine) as db:
        reconcile_signal_state(db)

    logger.info("MindLens backend started.")
    yield
    logger.info("MindLens backend shutting down.")


app = FastAPI(
    title="MindLens Backend",
    description="Counselor-facing early-signal platform for adolescent wellbeing",
    version="1.0.0",
    lifespan=lifespan,
)
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "MindLens Backend",
        "version": "1.0.0"
    }
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(intake.router)
app.include_router(personalization.router)


@app.get("/health")
def health_check():
    try:
        from sqlalchemy import text
        with Session(engine) as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "database": "disconnected"}
