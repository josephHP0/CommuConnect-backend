from fastapi import FastAPI
from app.db import init_db
from app.routers import auth

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {"message": "CommuConnect Backend OK"}

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])