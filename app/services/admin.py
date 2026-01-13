from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.user import User, Role


def count_admins(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.role == Role.ADMIN)
    ) or 0
