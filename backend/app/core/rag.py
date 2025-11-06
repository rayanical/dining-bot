from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.models import DiningHallMenu, User, Goal, DietaryConstraint
from app.core.retrieval import retrieve_food_items
from app.core.generation import generate_answer

def rag_answer(
    query: str,
    db: Session,
    user_id: Optional[int] = None
) -> Dict:
    """
    Main RAG function: Retrieves relevant food items using SQL and generates answer.
    
    Args:
        query: User's natural language question
        db: Database session
        user_id: Optional user ID to load profile
    
    Returns:
        Dict with 'answer' and 'sources' keys
    """
    # Load user profile if user_id provided
    user_profile = None
    if user_id is not None:  # Check explicitly for None, not truthiness (0 is valid)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Get dietary constraints
            constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()
            diets = []
            allergies = []
            for constraint in constraints:
                if constraint.constraint_type == "allergy":
                    allergies.append(constraint.constraint)
                elif constraint.constraint_type == "preference":
                    diets.append(constraint.constraint)
            
            # Get goals
            goals = db.query(Goal).filter(Goal.user_id == user_id).all()
            goal = goals[0].goal if goals and len(goals) > 0 else None
            
            user_profile = {
                "diets": diets,
                "allergies": allergies,
                "goal": goal,
            }
    
    # Phase 1: Retrieval (SQL query)
    food_items = retrieve_food_items(query, db, user_profile, limit=10)
    
    # Phase 2: Augmentation (format context)
    # Already done in generate_answer
    
    # Phase 3: Generation (LLM)
    answer = generate_answer(query, food_items, user_profile)
    
    # Format sources for response
    sources = []
    for item in food_items[:5]:  # Top 5 sources
        sources.append({
            "item": item.item,
            "dining_hall": item.dining_hall,
            "availability_today": item.availability_today or [],
            "calories": item.calories,
            "diet_types": item.diet_types or [],
        })
    
    return {
        "answer": answer,
        "sources": sources
    }

