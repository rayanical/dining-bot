from fastapi import APIRouter
from app.core.database import SessionLocal
from app.models import DiningHallMenu
from app.core.query_parser import ai_parse_query
from app.core.retrieval import retrieve_food_items
from sqlalchemy import text

router = APIRouter()


@router.get("/")
def test_endpoint():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * from users"))
        return {"message": f"DB connection working! Result: {result.all()}"}
    finally:
        db.close()


@router.get("/db-stats")
def db_stats():
    """Get database statistics about food items"""
    db = SessionLocal()
    try:
        total_items = db.query(DiningHallMenu).count()
        
        dining_halls = db.query(DiningHallMenu.dining_hall).distinct().all()
        hall_counts = {}
        for hall in dining_halls:
            count = db.query(DiningHallMenu).filter(DiningHallMenu.dining_hall == hall[0]).count()
            hall_counts[hall[0]] = count

        sample_items = db.query(DiningHallMenu).limit(5).all()
        samples = []
        for item in sample_items:
            samples.append({
                "item": item.item,
                "dining_hall": item.dining_hall,
                "calories": item.calories,
                "diet_types": item.diet_types,
                "availability_today": item.availability_today,
            })
        
        return {
            "total_items": total_items,
            "dining_halls": hall_counts,
            "sample_items": samples
        }
    finally:
        db.close()


@router.get("/test-query/{query_text}")
def test_query(query_text: str):
    """Test query parsing and retrieval without LLM generation"""
    db = SessionLocal()
    try:
        intent = ai_parse_query(query_text, None)
        filters = intent.filters.model_dump()
        items = retrieve_food_items(query_text, db, limit=10)
        results = []
        for item in items:
            results.append({
                "item": item.item,
                "dining_hall": item.dining_hall,
                "calories": item.calories,
                "diet_types": item.diet_types,
                "allergens": item.allergens,
                "availability_today": item.availability_today,
            })
        
        sample_all = db.query(DiningHallMenu).limit(3).all()
        sample_data = []
        for item in sample_all:
            sample_data.append({
                "item": item.item,
                "dining_hall": item.dining_hall,
                "availability_today": item.availability_today,
            })
        
        return {
            "query": query_text,
            "intent": intent.model_dump(),
            "parsed_filters": filters,
            "items_found": len(items),
            "items": results,
            "sample_db_data": sample_data,
            "debug": {
                "meal_filter": intent.filters.meals,
                "dining_hall_filter": intent.filters.dining_halls,
                "diet_filters": intent.filters.dietary_restrictions,
            }
        }
    finally:
        db.close()
