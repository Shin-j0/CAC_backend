import uuid
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, desc

from app.core.deps import get_db, get_current_admin, get_current_superadmin
from app.schemas.user import RoleUpdate

from app.models.user import User, Role
from app.models.admin_log import AdminAction, AdminActionLog

from app.services.admin_log import write_admin_log
from app.services.admin import count_admins



router = APIRouter(prefix="/admin", tags=["admin"])

# 관리자가 회원 권한을 변경하는 엔드포인트
@router.patch("/member/{user_id}/set_role")
def set_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted.is_(False)))

    # 해당 사용자가 존재하지 않는 경우
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 이미 해당 권한인 경우
    if user.role == data.role:
        raise HTTPException(
            status_code=400,
            detail=f"User already {user.role.value}"
        )
    
    # 자기 자신 권한 변경 금지
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # SUPERADMIN 승격/강등 금지
    if data.role == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot promote to SUPERADMIN")
    if user.role == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot change SUPERADMIN role")
    
    # ADMIN 승격은 SUPERADMIN만 가능
    if data.role == Role.ADMIN and current_admin.role != Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only SUPERADMIN can promote to ADMIN")


    # 마지막 ADMIN 강등 금지
    if user.role == Role.ADMIN and data.role != Role.ADMIN:
        admins = count_admins(db)
        if admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last ADMIN")

    before = user.role

    try:
        user.role = data.role
        write_admin_log(
            db,
            actor_id=current_admin.id,
            action=AdminAction.SET_ROLE,
            target_user_id=user.id,
            before_role=before.value,
            after_role=user.role.value,
        )
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")
    
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
    pending = db.scalars(select(User).where(User.role == Role.GUEST, User.is_deleted.is_(False))).all()
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
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted.is_(False)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != Role.GUEST:
        raise HTTPException(status_code=400, detail="User already approved")

    try:
        
        user.role = Role.MEMBER
        write_admin_log(
            db,
            actor_id=current_admin.id,
            action=AdminAction.APPROVE_USER,
            target_user_id=user.id,
            before_role=Role.GUEST.value,
            after_role=Role.MEMBER.value,
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

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
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted.is_(False)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 자기 자신 거절 금지
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot reject yourself")

    # GUEST가 아닌 경우 거절 불가
    if user.role != Role.GUEST:
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

    try:
        write_admin_log(
            db,
            actor_id=current_admin.id,
            action=AdminAction.REJECT_USER,
            target_user_id=user.id,
            before_role=user.role.value,
            after_role=Role.DELETED.value,
        )
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.role = Role.DELETED

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")


    return {
        "message": "User rejected and deleted",
        "data": user_snapshot,
    }

# 회원 삭제 엔드포인트
@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_superadmin),
):
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted.is_(False)))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 자기 자신 삭제 금지
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # SUPERADMIN 삭제 금지
    if user.role == Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete SUPERADMIN user")

    # 마지막 ADMIN 삭제 금지
    if user.role == Role.ADMIN:
        admins = count_admins(db)
        if admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last ADMIN")

    user_snapshot = {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "student_id": user.student_id,
        "role": user.role.value,
    }

    try:
        write_admin_log(
            db,
            actor_id=current_admin.id,
            action=AdminAction.DELETE_USER,
            target_user_id=user.id,
            before_role=user.role.value,
            after_role=Role.DELETED.value,
        )
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.role = Role.DELETED

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

    return {
        "message": "User deleted by admin",
        "data": user_snapshot,
    }

# 회원 상세 조회 엔드포인트(관리자 전용)
@router.get("/users/{user_id}/search")
def get_user_details(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted.is_(False)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "student_id": user.student_id,
        "phone": user.phone,
        "grade": user.grade,
        "role": user.role.value,
        "is_deleted": user.is_deleted,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }

# 전체 회원 목록 조회 엔드포인트(관리자 전용)
@router.get("/users/all")
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    users = db.scalars(select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.student_id)
        ).all()
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

@router.get("/users/deleted")
def list_deleted_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    # 삭제된 회원 목록 조회(최근 삭제일 기준)
    users = db.scalars(select(User).where(User.is_deleted.is_(True)).order_by(desc(User.deleted_at))).all()
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
                "is_deleted": u.is_deleted,
                "deleted_at": u.deleted_at.isoformat() if u.deleted_at else None,
            }
            for u in users
        ]
    }

# 관리자 활동 로그 조회 엔드포인트
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


