from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.rag import rag_answer

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[int] = None  # Optional: for personalized responses

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat endpoint that uses RAG to answer user questions about dining halls.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = rag_answer(req.query.strip(), db, user_id=req.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

