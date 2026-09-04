import uuid
import random
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models.case import StudentCase, CaseStatus
from app.models.rater import RaterType
from app.models.assessment import Question
from app.services import intake_service
from app.api.intake import submit_intake

def seed_demo_cases():
    with Session(engine) as db:
        # We need the Org ID to create cases
        from seed import DEV_ORG_ID
        
        # Define 3 demo cases with different scenarios
        demo_cases = [
            {
                "name": "Alex Morgan",
                "ref": "MF-0241",
                "responses": {
                    RaterType.PARENT: {"baseline": 4, "variance": 1},
                    RaterType.TEACHER: {"baseline": 2, "variance": 1},
                    RaterType.ADOLESCENT: {"baseline": 3, "variance": 1}
                } # Will cause meaningful divergence
            },
            {
                "name": "Jordan Taylor",
                "ref": "MF-0238",
                "responses": {
                    RaterType.PARENT: {"baseline": 3, "variance": 1},
                    RaterType.TEACHER: None, # Simulate waiting for teacher
                    RaterType.ADOLESCENT: {"baseline": 3, "variance": 1}
                }
            },
            {
                "name": "Riley Chen",
                "ref": "MF-0232",
                "responses": {
                    RaterType.PARENT: {"baseline": 5, "variance": 0},
                    RaterType.TEACHER: {"baseline": 5, "variance": 0},
                    RaterType.ADOLESCENT: {"baseline": 5, "variance": 0}
                } # High scores across the board
            }
        ]

        questions = db.exec(select(Question).where(Question.active == True)).all()
        if not questions:
            print("No questions found. Please run seed.py first.")
            return

        for case_data in demo_cases:
            print(f"Generating case: {case_data['name']}")
            
            # 1. Create the case
            case = StudentCase(
                organization_id=DEV_ORG_ID,
                display_name=case_data['name'],
                external_reference=case_data['ref'],
                status=CaseStatus.WAITING_FOR_RESPONSES,
            )
            db.add(case)
            db.commit()
            db.refresh(case)

            # 2. Generate intakes
            intakes = intake_service.create_intake_sessions(case.id, db)
            
            # 3. Simulate answering questions
            for intake in intakes:
                rater = RaterType(intake["rater_type"])
                rater_sim = case_data["responses"].get(rater)
                
                if rater_sim is None:
                    continue # Skip this rater to simulate 'WAITING_FOR_RESPONSES'
                
                print(f"  Simulating {rater.value} answers...")
                
                token = intake["token"]
                for q in questions:
                    # Randomize answer based on rater profile to create realistic data
                    val = rater_sim["baseline"] + random.choice([-rater_sim["variance"], 0, rater_sim["variance"]])
                    val = max(1, min(5, val)) # Keep within 1-5 likert scale
                    
                    intake_service.save_response(token, q.id, val, db)
                
                # Submit the intake
                submit_intake(token, db)
            
            print(f"Case {case_data['name']} complete!\n")

if __name__ == "__main__":
    seed_demo_cases()
    print("Demo cases seeded successfully.")
