import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_member, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, Role


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
def profile(current_user: User = Depends(get_current_member)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "student_id": current_user.student_id,
        "phone": current_user.phone,
        "grade": current_user.grade,
    }


@router.get("/users")
def list_all_users(
    db: Session = Depends(get_db),
    member: User = Depends(get_current_member),
):
    users = db.scalars(select(User).where(User.role == Role.MEMBER)).all()
    return [
        {
            "email": u.email,
            "name": u.name,
            "student_id": u.student_id,
            "phone": u.phone,
            "grade": u.grade,
            "role": u.role,
        }
        for u in users
    ]

