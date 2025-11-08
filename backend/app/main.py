from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import test, chat, users
from app.core.database import engine, Base

app = FastAPI(title="Dining Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # In case frontend runs on 3001
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Tables are already created in Supabase, so we don't create them here
# If you need to create tables locally, uncomment the line below:
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

app.include_router(test.router, prefix="/api/test", tags=["Test"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Dining Bot API is running!"}
