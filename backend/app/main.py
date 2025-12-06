from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import test, chat, users, food

app = FastAPI(title="Dining Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # frontend alternate port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(test.router, prefix="/api/test", tags=["Test"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(food.router, prefix="/api/food", tags=["Food"])

@app.get("/")
def root():
    return {"message": "Dining Bot API is running!"}
