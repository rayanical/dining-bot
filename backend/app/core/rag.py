from typing import Dict, Optional, Iterator, List
from sqlalchemy.orm import Session
from app.models import User, Goal, DietaryConstraint
from app.core.retrieval import retrieve_food_items
from app.core.generation import generate_answer

# Map user-facing diet names to database diet_types values
DIET_NAME_MAPPING = {
    "vegan": "Plant Based",
    "plant based": "Plant Based",
    "plant-based": "Plant Based",
    "vegetarian": "Vegetarian",
    "halal": "Halal",
    "kosher": "Kosher",
    "gluten-free": "Gluten-Free",
    "gluten free": "Gluten-Free",
}


def _normalize_diet(diet: str) -> str:
    """Normalize a diet preference to match database diet_types values."""
    return DIET_NAME_MAPPING.get(diet.lower(), diet)


def _get_user_profile(db: Session, user_id: Optional[str] = None) -> Optional[Dict]:
    """Fetch a user's dietary profile from the database.

    Args:
        db (Session): SQLAlchemy database session.
        user_id (Optional[str]): The Supabase user ID. If None, no lookup is performed.

    Returns:
        Optional[Dict]: A dictionary with keys "diets" (List[str]), "allergies" (List[str]),
        and "goal" (Optional[str]) when the user exists; otherwise None.
    """
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()
    
    # Normalize diet names to match database values (e.g., "Vegan" -> "Plant Based")
    raw_diets = [c.constraint for c in constraints if c.constraint_type == "preference"]
    diets = [_normalize_diet(d) for d in raw_diets]
    
    allergies = [c.constraint for c in constraints if c.constraint_type == "allergy"]
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    goal = goals[0].goal if goals else None
    return {"diets": diets, "allergies": allergies, "goal": goal}

def rag_answer_stream(
    query: str,
    db: Session,
    user_id: Optional[str] = None,
    history_text: Optional[str] = None,
) -> Iterator[str]:
    """Run the RAG pipeline and stream the generated answer as chunks.

    The function retrieves relevant menu items for the current day based on the
    user's natural language question and optional profile, then streams an LLM
    answer in text chunks suitable for HTTP streaming responses.

    Args:
        query (str): The user's natural language question.
        db (Session): SQLAlchemy database session.
        user_id (Optional[str]): Optional Supabase user ID to enrich retrieval with
            user-specific diets, allergies, and goals.

    Returns:
        Iterator[str]: A generator that yields segments of the assistant's response.
    """
    user_profile = _get_user_profile(db, user_id)
    food_items = retrieve_food_items(query, db, user_profile, limit=10)
    return generate_answer(query, food_items, user_profile, history_text)

