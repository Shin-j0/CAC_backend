from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.core.deps import get_db, get_current_admin
from app.schemas.user import RoleUpdate, RoleUpdate
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/ping")
def admin_ping(admin: User = Depends(get_current_admin)):
    return {"ok": True, "admin_email": admin.email, "role": admin.role}


@router.patch("/users/{user_id}/role")
def set_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == data.role:
        raise HTTPException(
            status_code=400,
            detail=f"User already {user.role}"
        )

    user.role = data.role
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role
    }

@router.get("/pending-users")
def list_pending_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    pending = db.scalars(select(User).where(User.role == "GUEST")).all()
    return [
        {"id": str(u.id), "email": u.email, "name": u.name, "student_id": u.student_id}
        for u in pending
    ]
