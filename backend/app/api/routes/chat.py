from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.rag import rag_answer_stream
from fastapi.responses import StreamingResponse

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
    """Streaming chat endpoint that yields text chunks."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        stream_gen = rag_answer_stream(req.query.strip(), db, user_id=req.user_id)
        return StreamingResponse(stream_gen, media_type="text/plain")
    except Exception as e:
        return StreamingResponse(iter([f"Error processing query: {str(e)}"]), media_type="text/plain", status_code=500)

