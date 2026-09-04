import uuid
from sqlmodel import Session, select
from app.database import create_db_and_tables, engine
from app.main import seed_questionnaire_if_needed
from app.models.counselor import Organization, User, UserRole
from app.models.evidence import Evidence
from app.utils.security import hash_password

DEV_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')
DEV_COUNSELOR_ID = uuid.UUID('00000000-0000-0000-0000-000000000002')

def seed():
    create_db_and_tables()
    seed_questionnaire_if_needed()
    
    with Session(engine) as db:
        # Seed Organization
        org = db.get(Organization, DEV_ORG_ID)
        if not org:
            org = Organization(id=DEV_ORG_ID, name="Greenwood High School")
            db.add(org)
            db.commit()
            
        # Seed Counselor
        user = db.get(User, DEV_COUNSELOR_ID)
        if not user:
            user = User(
                id=DEV_COUNSELOR_ID,
                organization_id=DEV_ORG_ID,
                name="Sarah Chen",
                email="sarah.chen@greenwood.edu",
                password_hash=hash_password("MindLens2024!"),
                role=UserRole.COUNSELOR,
                is_active=True
            )
            db.add(user)
            db.commit()
            
        # Seed Evidence
        ev = db.exec(select(Evidence).where(Evidence.evidence_code == "EVD_ATTN_PARENT_TEACHER_001")).first()
        if not ev:
            ev = Evidence(
                evidence_code="EVD_ATTN_PARENT_TEACHER_001",
                title="Parent-Teacher discrepancy in attention ratings predicts multi-setting support needs.",
                source="Journal of Clinical Child & Adolescent Psychology",
                source_type="Peer Reviewed",
                evidence_certainty="VERY_LOW",
                study_count=3,
                sample_size=1200,
                association_value="Moderate",
                limitation="Synthetic Hackathon Record",
            )
            db.add(ev)
            db.commit()

if __name__ == "__main__":
    seed()
    print("Database seeded successfully.")
