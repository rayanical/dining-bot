from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.core.database import SessionLocal
from app.core.nutrition import goal_to_targets
from app.models import User, Goal, DietaryConstraint, DietHistory
from app.schemas import UserProfileCreate, FoodLogCreate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Profile Routes (Keep as is) ---
@router.post("/profile")
def create_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    try:
        # 1. Get or create user
        user = db.query(User).filter(User.id == profile.user_id).first()
        if not user:
            user = User(id=profile.user_id, email=profile.email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. CLEAR OLD DATA
        db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user.id).delete()
        db.query(Goal).filter(Goal.user_id == user.id).delete()

        # Save Goal
        if profile.goal:
            db.add(Goal(user_id=user.id, goal=profile.goal, success_metric="TBD", progress="0%"))

        # Save Diets
        for diet in profile.diets:
            db.add(DietaryConstraint(user_id=user.id, constraint=diet, constraint_type="preference"))
        
        # Save Allergies
        for allergy in profile.allergies:
            if allergy.strip():
                 db.add(DietaryConstraint(user_id=user.id, constraint=allergy.strip(), constraint_type="allergy"))

        # Save Cuisines
        for cuisine in profile.liked_cuisines:
             db.add(DietaryConstraint(user_id=user.id, constraint=cuisine, constraint_type="cuisine"))

        # Save Dislikes
        if profile.dislikes and profile.dislikes.strip():
             db.add(DietaryConstraint(user_id=user.id, constraint=profile.dislikes.strip(), constraint_type="dislike"))

        db.commit()
        return {"status": "success"}

    except Exception as e:
        db.rollback()
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/profile/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()
    liked_cuisines = [c.constraint for c in constraints if c.constraint_type == 'cuisine']
    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
        "goal": goal.goal if goal else None,
        "liked_cuisines": liked_cuisines,
        "dietary_constraints": [
            {"constraint": c.constraint, "constraint_type": c.constraint_type}
            for c in constraints
        ],
    }

# --- LOGGING ROUTES ---

@router.post("/{user_id}/log-food")
def log_food(user_id: str, payload: FoodLogCreate, db: Session = Depends(get_db)):
    """Log a food entry."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        log_date = date.today()
        if payload.date:
            log_date = date.fromisoformat(payload.date)

        entry = DietHistory(
            user_id=user_id,
            date=log_date,
            item=payload.item_name,
            mealtime=payload.meal_type.lower(),
            calories=payload.calories,
            protein_g=payload.protein or 0.0,
            allergens=[],
            diet_types=[],
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return {"status": "success", "id": entry.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: Get Daily Log List ---
@router.get("/{user_id}/log")
def get_daily_log(
    user_id: str, 
    date_str: str = Query(..., description="Date in YYYY-MM-DD format"), 
    db: Session = Depends(get_db)
):
    """Get the list of food items logged for a specific date."""
    try:
        target_date = date.fromisoformat(date_str)
        logs = db.query(DietHistory).filter(
            DietHistory.user_id == user_id,
            DietHistory.date == target_date
        ).all()
        
        return logs
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@router.get("/{user_id}/daily-summary")
def get_daily_summary(user_id: str, date_param: date = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    """Return calorie totals."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        summary_date = date_param or date.today()
        goal = db.query(Goal).filter(Goal.user_id == user_id).first()
        cal_target, protein_target = goal_to_targets(goal.goal if goal else None)

        entries = (
            db.query(DietHistory)
            .filter(DietHistory.user_id == user_id)
            .filter(DietHistory.date == summary_date)
            .all()
        )

        calories_total = sum(e.calories or 0 for e in entries)
        protein_total = sum(e.protein_g or 0 for e in entries)

        return {
            "status": "success",
            "date": summary_date.isoformat(),
            "goal": goal.goal if goal else None,
            "calories": {"total": calories_total, "target": cal_target},
            "protein": {"total": protein_total, "target": protein_target},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))