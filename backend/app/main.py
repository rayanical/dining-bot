from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import test, menu


app = FastAPI(title="Dining Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test.router, prefix="/api/test", tags=["Test"])
app.include_router(menu.router, prefix="/api/menu", tags=["Menu"])

@app.get("/")
def root():
    return {"message": "Dining Bot API is running!"}
