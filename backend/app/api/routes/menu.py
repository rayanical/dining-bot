from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import SessionLocal
from app.data.models import FoodItem

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_all_menus(db: Session = Depends(get_db)):
    """
    Fetches all food items currently in the database.
    """
    menu_items = db.query(FoodItem).all()
    return menu_items

@router.get("/{dining_hall}")
def get_menu_for_hall(dining_hall: str, db: Session = Depends(get_db)):
    """
    Fetches all food items for a specific dining hall.
    """
    # Use ilike for case-insensitive matching
    menu_items = db.query(FoodItem).filter(FoodItem.dining_hall.ilike(f"%{dining_hall}%")).all()
    return menu_items