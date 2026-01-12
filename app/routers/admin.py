from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, desc

import uuid

from app.core.deps import get_db, get_current_admin, get_current_superadmin
from app.schemas.user import RoleUpdate

from app.models.user import User, Role
from app.models.admin_log import AdminAction, AdminActionLog

from app.services.admin_log import write_admin_log

router = APIRouter(prefix="/admin", tags=["admin"])


# admin 권한을 가진 관리자 수 세는 헬퍼 함수
def _count_admins(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role.value == Role.ADMIN)) or 0

# 관리자가 회원 권한을 변경하는 엔드포인트
@router.patch("/member/{user_id}/set_role")
def set_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))

    # 해당 사용자가 존재하지 않는 경우
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 이미 해당 권한인 경우
    if user.role.value == data.role.value:
        raise HTTPException(
            status_code=400,
            detail=f"User already {user.role.value}"
        )
    
    # 자기 자신 권한 변경 금지
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # SUPERADMIN 승격/강등 금지
    if data.role.value == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot promote to SUPERADMIN")
    if user.role.value == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot change SUPERADMIN role")
    
    # ADMIN 승격은 SUPERADMIN만 가능
    if data.role.value == Role.ADMIN and current_admin.role.value != Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only SUPERADMIN can promote to ADMIN")


    # 마지막 ADMIN 강등 금지
    if user.role.value == Role.ADMIN and data.role.value != Role.ADMIN:
        admins = _count_admins(db)
        if admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last ADMIN")

    before = user.role.value
    user.role.value = data.role.value

    write_admin_log(
        db,
        actor_id=current_admin.id,
        action=AdminAction.SET_ROLE,
        target_user_id=user.id,
        before_role=str(before),
        after_role=str(user.role.value),
    )


    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    
    return {
        "message": "Role updated",
        "data": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
        },
    }


# 승인 대기 중인 회원 목록을 조회하는 엔드포인트
@router.get("/guest/pending")
def list_pending_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    pending = db.scalars(select(User).where(User.role.value == Role.GUEST)).all()
    return {
        "data": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "student_id": u.student_id,
            }
            for u in pending
        ]
    }

# 대기자 승인 엔드포인트
@router.post("/guest/{user_id}/approve")
def approve_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.value != Role.GUEST:
        raise HTTPException(status_code=400, detail="User already approved")

    user.role.value = Role.MEMBER

    write_admin_log(
        db,
        actor_id=current_admin.id,
        action=AdminAction.APPROVE_USER,
        target_user_id=user.id,
        before_role=str(Role.GUEST.value),
        after_role=str(Role.MEMBER.value),
    )


    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
    "message": "User approved",
    "data": {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "before_role": Role.GUEST.value,
        "after_role": Role.MEMBER.value,
    },
}

# 대기자 거절 엔드포인트
@router.post("/guest/{user_id}/reject")
def reject_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot reject yourself")

    if user.role.value != Role.GUEST:
        raise HTTPException(
            status_code=400,
            detail=f"User already {user.role.value}"
        )
    
    user_snapshot = {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "student_id": user.student_id,
        "role": user.role.value,
    }

    write_admin_log(
        db,
        actor_id=current_admin.id,
        action=AdminAction.REJECT_USER,
        target_user_id=user.id,
        before_role=str(user.role.value),
        after_role=None,
    )

    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "message": "User rejected and deleted",
        "data": user_snapshot,
    }

# 전체 회원 목록 조회 엔드포인트(관리자 전용)
@router.get("/users")
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    users = db.scalars(select(User)).all()
    return {
        "data": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "student_id": u.student_id,
                "phone": u.phone,
                "grade": u.grade,
                "role": u.role.value,
            }
            for u in users
        ]
    }


@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_superadmin),
):
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    if user.role.value == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete SUPERADMIN user")

    # 마지막 ADMIN 삭제 금지
    if user.role.value == Role.ADMIN:
        admins = _count_admins(db)
        if admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last ADMIN")

    user_snapshot = {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "student_id": user.student_id,
        "role": user.role.value,
    }

    write_admin_log(
        db,
        actor_id=current_admin.id,
        action=AdminAction.DELETE_USER,
        target_user_id=user.id,
        before_role=str(user.role.value),
        after_role=None,
    )

    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "message": "User deleted by admin",
        "data": user_snapshot,
    }


@router.get("/logs")
def list_admin_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    limit = max(1, min(limit, 200))

    Actor = aliased(User)
    Target = aliased(User)

    rows = db.execute(
        select(AdminActionLog, Actor, Target)
        .join(Actor, Actor.id == AdminActionLog.actor_id)
        .outerjoin(Target, Target.id == AdminActionLog.target_user_id)
        .order_by(desc(AdminActionLog.created_at))
        .limit(limit)
    ).all()

    result = []
    for log, actor, target in rows:
        result.append(
            {
                "id": str(log.id),
                "created_at": log.created_at.isoformat(),
                "action": log.action,
                "before_role": log.before_role,
                "after_role": log.after_role,
                "actor": {
                    "id": str(actor.id),
                    "email": actor.email,
                    "name": actor.name,
                    "role": actor.role.value,
                },
                "target": (
                    {
                        "id": str(target.id),
                        "email": target.email,
                        "name": target.name,
                        "role": target.role.value,
                    }
                    if target
                    else None
                ),
            }
        )
    return {
        "data": result,
        "meta": {
            "limit": limit,
            "count": len(result),
        },
    }


