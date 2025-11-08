from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import User, Goal, DietaryConstraint
from app.schemas import UserProfileCreate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/profile")
def create_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    try:
        # 1. Ensure user exists in our public table
        user = db.query(User).filter(User.id == profile.user_id).first()
        if not user:
            user = User(id=profile.user_id, email=profile.email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Clear old data to allow updates
        db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user.id).delete()
        db.query(Goal).filter(Goal.user_id == user.id).delete()
        
        # 3. Add new constraints
        for diet in profile.diets:
            db.add(DietaryConstraint(user_id=user.id, constraint=diet, constraint_type="preference"))
        
        for allergy in profile.allergies:
            if allergy.strip():
                 db.add(DietaryConstraint(user_id=user.id, constraint=allergy.strip(), constraint_type="allergy"))

        # 4. Add new goal
        if profile.goal:
            # Providing default values for required non-nullable fields
            db.add(Goal(user_id=user.id, goal=profile.goal, success_metric="TBD", progress="0%"))
            
        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        db.rollback()
        # print(f"Error creating profile: {e}") # Uncomment for debugging
        raise HTTPException(status_code=500, detail=str(e))