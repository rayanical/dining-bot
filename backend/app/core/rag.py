from typing import Dict, Optional, List, Iterator
from sqlalchemy.orm import Session
from app.models import DiningHallMenu, User, Goal, DietaryConstraint
from app.core.retrieval import retrieve_food_items
from app.core.generation import generate_answer

def _get_user_profile(db: Session, user_id: Optional[str] = None) -> Optional[Dict]:
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()
    diets = [c.constraint for c in constraints if c.constraint_type == "preference"]
    allergies = [c.constraint for c in constraints if c.constraint_type == "allergy"]
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    goal = goals[0].goal if goals else None
    return {"diets": diets, "allergies": allergies, "goal": goal}

def rag_answer_stream(
    query: str,
    db: Session,
    user_id: Optional[str] = None
) -> Iterator[str]:
    """Streaming RAG pipeline: retrieve items then yield LLM chunks."""
    user_profile = _get_user_profile(db, user_id)
    food_items = retrieve_food_items(query, db, user_profile, limit=10)
    return generate_answer(query, food_items, user_profile)

