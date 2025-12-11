from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.core.database import SessionLocal
from app.core.nutrition import goal_to_targets
from app.models import User, Goal, DietaryConstraint, DietHistory
from app.schemas import UserProfileCreate, FoodLogCreate, CustomGoalUpdate

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
    dislike_entry = next((c.constraint for c in constraints if c.constraint_type == 'dislike'), "")
    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
        "goal": goal.goal if goal else None,
        "liked_cuisines": liked_cuisines,
        "dislikes": dislike_entry,
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
def get_daily_summary(
    user_id: str,
    date_param: date = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        summary_date = date_param or date.today()
        goal = db.query(Goal).filter(Goal.user_id == user_id).first()
        
        # Get targets with defaults
        if goal and goal.calories_target is not None and goal.protein_target is not None:
            cal_target = goal.calories_target
            protein_target = goal.protein_target
            # Use defaults for carbs/fat if custom goals don't store them (future proofing: add columns to Goal table)
            _, _, carbs_target, fat_target = goal_to_targets(goal.goal)
        else:
            cal_target, protein_target, carbs_target, fat_target = goal_to_targets(goal.goal if goal else None)

        entries = (
            db.query(DietHistory)
            .filter(DietHistory.user_id == user_id)
            .filter(DietHistory.date == summary_date)
            .all()
        )

        calories_total = sum(e.calories or 0 for e in entries)
        protein_total = sum(e.protein_g or 0 for e in entries)
        # Note: DietHistory model currently doesn't store carbs/fat explicitly in columns unless we migrate.
        # But for now, we can assume 0 or try to fetch if we added columns.
        # Let's check DietHistory model definition again. It does NOT have carbs/fat columns yet.
        # So we will return 0 for total carbs/fat for now to avoid breaking,
        # OR we need to update DietHistory model to store them.
        # Given "DietHistory" only has: calories, protein_g, allergens, diet_types.
        # We cannot track daily consumed carbs/fat without a DB migration.
        # However, the user asked to "put in other nutritions".
        # I will return the Targets at least, and 0 for total, so the frontend doesn't crash.
        
        carbs_total = 0 # Placeholder until DB migration
        fat_total = 0   # Placeholder until DB migration

        history = [
            {
                "id": e.id,
                "item": e.item,
                "calories": e.calories,
                "protein": e.protein_g,
                "meal": e.mealtime,
            }
            for e in entries
        ]

        return {
            "status": "success",
            "date": summary_date.isoformat(),
            "goal": goal.goal if goal else None,
            "calories": {"total": calories_total, "target": cal_target},
            "protein": {"total": protein_total, "target": protein_target},
            "carbs": {"total": carbs_total, "target": carbs_target},
            "fat": {"total": fat_total, "target": fat_target},
            "history": history,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{user_id}/goals")
def update_user_goals(user_id: str, payload: CustomGoalUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    if not goal:
        goal = Goal(user_id=user_id, goal=None, success_metric="custom", progress="0%")
        db.add(goal)

    goal.calories_target = payload.calories
    goal.protein_target = payload.protein

    db.commit()
    db.refresh(goal)

    return {
        "status": "success",
        "calories": goal.calories_target,
        "protein": goal.protein_target
    }

@router.delete("/{user_id}/log-food/{log_id}")
def delete_food_entry(user_id: str, log_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(DietHistory)
        .filter(DietHistory.id == log_id)
        .filter(DietHistory.user_id == user_id)
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")

    db.delete(entry)
    db.commit()

    return {"status": "success", "message": "Entry deleted"}