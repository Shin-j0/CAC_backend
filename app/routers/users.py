import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_member, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, Role
from starlette import status


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
def profile(current_user: User = Depends(get_current_member)):
    return {
        "name": current_user.name,
        "email": current_user.email,
        "student_id": current_user.student_id,
        "grade": current_user.grade,
        "phone": current_user.phone,
        "role": current_user.role.value,
    }


@router.get("/all")
def list_all_users(
    db: Session = Depends(get_db),
    member: User = Depends(get_current_member),
):
    users = db.scalars(
        select(User)
        .where(User.role == Role.MEMBER, User.is_deleted.is_(False))
        .order_by(User.student_id)
).all()
        
    return [
        {
            "name": u.name,
            "student_id": u.student_id,
            "grade": u.grade,
        }
        for u in users
    ]