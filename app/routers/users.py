"""
users.py

회원(Member) 전용 사용자 정보 조회 API 모음.

이 파일은 로그인한 일반 회원이
본인의 기본 프로필 정보와
동아리 내 다른 회원들의 공개 정보를 조회하기 위한 기능을 담당한다.

관리자용 사용자 관리 기능(admin.py)과 분리하여,
권한 범위와 노출 가능한 데이터 범위를 명확히 하기 위한 구조이다.

주요 기능:
- 본인 프로필 정보 조회
- 동아리 소속 회원 목록 조회 (공개 정보만)

설계 원칙:
- MEMBER 이상 권한만 접근 가능
- 개인정보 보호를 위해 최소한의 정보만 노출
- Soft Delete(is_deleted=True)된 회원은 기본적으로 제외

관련 파일:
- app.models.user          : User / Role 모델
- app.core.deps            : 회원 권한 인증(get_current_member)
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_member, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, Role
from starlette import status

router = APIRouter(prefix="/users", tags=["users"])

"""
회원 본인 프로필 조회 API

- 로그인한 회원 본인의 정보만 조회
- 이름, 이메일, 학번, 학년, 전화번호, 권한(role) 반환

"""
@router.get("/profile")
def profile(current_user: User = Depends(get_current_member)):
    return {
        "name": current_user.name,
        "email": current_user.email,
        "student_id": current_user.student_id,
        "grade": current_user.grade,
        "phone": current_user.phone,
    }

"""
동아리 회원 목록 조회 API (회원용)

- 동아리 소속 MEMBER 회원만 조회
- Soft Delete되지 않은 활성 회원만 포함
- 학번 기준 오름차순 정렬
- 공개 가능한 최소 정보만 반환 (이름, 학번, 학년)

"""
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
