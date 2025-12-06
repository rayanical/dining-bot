from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
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

@router.post("/profile")
def create_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    """Create or update a user's dining profile.

    Persists the user's email, dietary constraints (diets and allergies), and a
    goal. Existing constraints and goal records are replaced to reflect the new
    submission.

    Args:
        profile (UserProfileCreate): Payload containing user_id, email, diets,
            allergies, and goal.
        db (Session): SQLAlchemy session dependency.

    Returns:
        dict: {"status": "success"} on success.

    Raises:
        HTTPException: 500 if database operations fail.
    """
    try:
        user = db.query(User).filter(User.id == profile.user_id).first()
        if not user:
            user = User(id=profile.user_id, email=profile.email)
            db.add(user)
            db.commit()
            db.refresh(user)

        db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user.id).delete()
        db.query(Goal).filter(Goal.user_id == user.id).delete()

        for diet in profile.diets:
            db.add(DietaryConstraint(user_id=user.id, constraint=diet, constraint_type="preference"))
        
        for allergy in profile.allergies:
            if allergy.strip():
                 db.add(DietaryConstraint(user_id=user.id, constraint=allergy.strip(), constraint_type="allergy"))

        if profile.goal:
            # Providing default values for required non-nullable fields
            db.add(Goal(user_id=user.id, goal=profile.goal, success_metric="TBD", progress="0%"))
            
        db.commit()
        return {"status": "success"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/log-food")
def log_food(user_id: str, payload: FoodLogCreate, db: Session = Depends(get_db)):
    """Log a food entry to the user's diet history."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        entry = DietHistory(
            user_id=user_id,
            date=payload.date,
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

@router.get("/profile/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Return a lightweight snapshot of a user's profile.

    Args:
        user_id (str): Supabase user ID.
        db (Session): SQLAlchemy session dependency.

    Returns:
        dict: JSON-safe dict with status, user_id, email, goal, and
        dietary_constraints (list of {constraint, constraint_type}).

    Raises:
        HTTPException: 404 if the user does not exist; 500 for unexpected errors.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()

    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
        "goal": goal.goal if goal else None,
        "dietary_constraints": [
            {"constraint": c.constraint, "constraint_type": c.constraint_type}
            for c in constraints
        ],
    }


@router.get("/{user_id}/daily-summary")
def get_daily_summary(user_id: str, date_param: date = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    """Return calorie and protein totals for a user on a given date plus goal-based targets."""
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
    except HTTPException:
        raise
    except Exception as e:
        # Surface error for easier debugging in frontend
        raise HTTPException(status_code=500, detail=str(e))