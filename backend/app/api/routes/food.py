from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal
from app.models import DiningHallMenu
from app.core.retrieval import retrieve_food_items
from app.schemas import FoodItem

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/search", response_model=List[FoodItem])
def search_food(
    q: Optional[str] = Query(None, description="Search term"),
    dining_hall: Optional[str] = Query(None),
    meal: Optional[str] = Query(None),
    diets: Optional[List[str]] = Query(None),
    allergies: Optional[List[str]] = Query(None),
    min_calories: Optional[float] = Query(None),
    max_calories: Optional[float] = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    hall_filter = dining_hall.capitalize() if dining_hall else None
    
    structured_filters = {
        "item_name": q,  # Pass text query as item_name filter
        "dining_hall": hall_filter,
        "meal": meal,
        "diets": diets or [],
        "allergies": allergies or [],
        "min_calories": min_calories,
        "max_calories": max_calories,
    }

    # Pass empty query string so we rely purely on structured_filters
    items = retrieve_food_items(
        query="", 
        db=db,
        limit=limit,
        structured_filters=structured_filters
    )
    return items

@router.get("/options")
def get_filter_options(db: Session = Depends(get_db)):
    halls_query = db.query(DiningHallMenu.dining_hall).distinct().all()
    dining_halls = sorted([h[0] for h in halls_query if h[0]])
    return {
        "dining_halls": dining_halls,
        "meals": ["Breakfast", "Lunch", "Dinner", "Late Night", "Brunch", "Grab' n Go"],
        "diets": ["Vegan", "Vegetarian", "Halal", "Kosher", "Gluten-Free", "Sustainable"]
    }