from fastapi import APIRouter
from app.core.database import SessionLocal
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
