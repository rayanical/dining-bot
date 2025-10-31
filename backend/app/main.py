from fastapi import FastAPI

from app.api.routes import test

app = FastAPI(title="Dining Bot API")

app.include_router(test.router, prefix="/api/test", tags=["Test"])


@app.get("/")
def root():
    return {"message": "Dining Bot API is running!"}
