from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db

from app.routers import auth, users, admin

app = FastAPI(title="Club Backend")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}

@app.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    value = db.execute(text("SELECT 1")).scalar_one()
    return {"db": "ok", "value": value}