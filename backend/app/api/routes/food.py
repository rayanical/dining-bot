from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.database import SessionLocal
from app.core.retrieval import retrieve_food_items
from app.core.rag import _get_user_profile

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def search_food(q: str, limit: int = 10, user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Search dining hall menu items to assist with food logging."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_profile = _get_user_profile(db, user_id) if user_id else None

    try:
        items = retrieve_food_items(
            query=q,
            db=db,
            user_profile=user_profile,
            limit=limit,
            current_date=date.today(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    results = []
    for item in items:
        results.append({
            "id": item.id,
            "item": item.item,
            "dining_hall": item.dining_hall,
            "calories": item.calories,
            "protein_g": item.protein_g,
            "availability_today": item.availability_today,
            "diet_types": item.diet_types,
            "allergens": item.allergens,
        })

    return {"results": results}
