from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.deps import get_db
from app.routers import auth, users, admin, dues, admin_dues

app = FastAPI(title="Club Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(dues.router)
app.include_router(admin_dues.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    value = db.execute(text("SELECT 1")).scalar_one()
    return {"db": "ok", "value": value}
