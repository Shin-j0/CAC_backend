"""
auth.py

인증(Authentication) 및 계정 관리 API 모음.

이 파일은 회원 가입, 로그인, 토큰 재발급, 로그아웃과 같이
사용자 인증 흐름 전반을 담당한다.
JWT 기반 인증 방식을 사용하며, Access Token + Refresh Token 구조를 따른다.

주요 기능:
- 회원 가입 (탈퇴 계정 복구 포함)
- 로그인 및 토큰 발급
- Refresh Token 기반 Access Token 재발급
- 로그아웃 (Refresh Token 무효화)
- 회원 정보 수정 및 비밀번호 변경
- 회원 본인 탈퇴 (Soft Delete)

설계 원칙:
- Access Token은 Authorization Header로 전달
- Refresh Token은 HttpOnly Cookie로 관리
- Refresh Token Version을 이용해 강제 로그아웃 / 토큰 무효화 처리
- 회원 탈퇴는 Hard Delete가 아닌 Soft Delete 방식 사용

관련 파일:
- app.core.security        : 비밀번호 해시 / JWT 생성·검증
- app.core.deps            : 인증 의존성(get_current_member)
- app.models.user          : User / Role 모델
- app.schemas.auth         : 인증 관련 요청/응답

"""

import uuid
from jose import JWTError, ExpiredSignatureError
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_db, get_current_member
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

from app.models.user import User, Role
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, TokenResponse, DeleteMeRequest,
    EditProfileRequest, ChangePasswordRequest
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"

"""
회원 가입 API

- 이메일 기준으로 신규 회원 가입
- 탈퇴한 계정이 존재할 경우 계정을 복구하여 재가입 처리
- 동일 학번을 사용하는 활성 계정이 있으면 가입 불가
- 가입 시 기본 권한은 GUEST (관리자 승인 필요)

"""

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    # 활성 계정이 이미 있으면 가입 불가
    active = db.scalar(
        select(User).where(
            User.email == data.email,
            User.is_deleted.is_(False),
        )
    )
    if active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 탈퇴 계정이 있으면 복구
    deleted = db.scalar(
        select(User).where(
            User.email == data.email,
            User.is_deleted.is_(True),
        )
    )

    # 같은 학번을 다른 "활성 사용자"가 이미 쓰고 있으면 복구/가입 둘 다 막아야 함
    if data.student_id:
        student_active = db.scalar(
            select(User).where(
                User.student_id == data.student_id,
                User.is_deleted.is_(False),
            )
        )
        # 복구 대상(deleted)이 있고, 학번이 자기 자신이면 OK / 아니면 충돌
        if student_active and (not deleted or student_active.id != deleted.id):
            raise HTTPException(status_code=400, detail="Student ID already in use")

    try:
        # 탈퇴 계정이 있으면 복구
        if deleted:
            deleted.is_deleted = False
            deleted.deleted_at = None

            deleted.password_hash = get_password_hash(data.password)
            deleted.name = data.name
            deleted.student_id = data.student_id
            deleted.phone = data.phone
            deleted.grade = data.grade

            deleted.role = Role.GUEST

            db.commit()
            db.refresh(deleted)
            return {
                "data": {
                    "id": str(deleted.id),
                    "email": deleted.email,
                }
            }

        # 탈퇴 계정도 없으면 새로 생성
        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            name=data.name,
            student_id=data.student_id,
            phone=data.phone,
            grade=data.grade,
            role=Role.GUEST,
            is_deleted=False,
            deleted_at=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "data": {
                "id": str(user.id),
                "email": user.email,
            }
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")


"""
로그인 API

- 이메일 / 비밀번호 인증
- 승인되지 않은 GUEST 계정은 로그인 불가
- Access Token은 응답 바디로 반환
- Refresh Token은 HttpOnly Cookie로 설정

"""

@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):

    user = db.scalar(select(User).where(User.email == data.email, User.is_deleted.is_(False)))

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # guest는 로그인 불가
    if user.role == Role.GUEST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pending approval"
        )

    access = create_access_token(subject=str(user.id))
    refresh = create_refresh_token(subject=str(user.id), refresh_token_version=user.refresh_token_version)

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.COOKIE_SECURE,        # 로컬 False / HTTPS 운영 True
        samesite=settings.COOKIE_SAMESITE,    # "lax" 추천
        domain=settings.COOKIE_DOMAIN,        # 보통 None
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "data": {
            "access_token": access,
            "token_type": "bearer",
        }
    }

"""
Access Token 재발급 API

- Refresh Token 쿠키를 사용해 새로운 Access Token 발급
- Refresh Token Version이 일치하지 않으면 재발급 거부
- 재발급 시 Refresh Token을 회전(rotation)하여 보안 강화

"""

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        user_id, token_rtv = decode_refresh_token(token)
        user_uuid = uuid.UUID(user_id)
    except (ExpiredSignatureError, JWTError, ValueError):
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.scalar(
        select(User).where(
            User.id == user_uuid,
            User.is_deleted.is_(False),
        )
    )
    if not user:
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)
        raise HTTPException(status_code=401, detail="User not found")

    if token_rtv != user.refresh_token_version:
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    user.refresh_token_version += 1
    db.commit()
    db.refresh(user)

    new_access = create_access_token(subject=str(user.id))
    new_refresh = create_refresh_token(
        subject=str(user.id),
        refresh_token_version=user.refresh_token_version,
    )

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "data": {
            "access_token": new_access,
            "token_type": "bearer",
        }
    }

"""
로그아웃 API

- Refresh Token Version 증가로 기존 토큰 무효화
- 클라이언트의 Refresh Token 쿠키 삭제

"""

@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_member),
):
    try:
        user.refresh_token_version += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return Response(status_code=204)


"""
회원 본인 탈퇴 API

- 본인 비밀번호 확인 후 탈퇴 처리
- ADMIN / SUPERADMIN 계정은 탈퇴 불가
- Soft Delete 방식으로 처리 (is_deleted=True, role=DELETED)
- 탈퇴 시 모든 Refresh Token 무효화

"""

@router.delete("/me")
def delete_me(
    data: DeleteMeRequest,
    response: Response,
    db: Session = Depends(get_db),
    user : User = Depends(get_current_member),
):
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    if user.role in (Role.ADMIN, Role.SUPERADMIN):
        raise HTTPException(status_code=403, detail="Admin users cannot delete")

    if user.is_deleted:
        return {
            "data": {
                "status": "already_deleted",
            }
        }

    try:
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.role = Role.DELETED

        user.refresh_token_version += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return {
        "data": {
            "status": "deleted",
        }
    }

"""
회원 정보 수정 API

- 이름 / 전화번호 / 학년 정보 수정
- 변경 사항이 없으면 요청 거부
- 현재 사용자 비밀번호 확인 필수

"""

@router.patch("/edit")
def edit_profile(
    data: EditProfileRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_member),
):
    # 변경 사항 없으면 수정 x
    changed = any([
        data.name is not None,
        data.phone is not None,
        data.grade is not None,
        data.current_password is not None,
    ])
    if not changed:
        raise HTTPException(status_code=400, detail="No changes provided")

    # 1) 현재 비밀번호로 본인 확인
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    # 2) 프로필 부분 업데이트 (None이면 기존 유지)
    if data.name is not None:
        user.name = data.name
    if data.phone is not None:
        user.phone = data.phone
    if data.grade is not None:
        user.grade = data.grade

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

    return {
        "data": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "student_id": user.student_id,
            "phone": user.phone,
            "grade": user.grade,
            "role": user.role.value,
        },
    }

"""
비밀번호 변경 API

- 현재 비밀번호 확인 필수
- 새 비밀번호는 기존 비밀번호와 달라야 함
- 비밀번호 변경 시 Refresh Token 무효화

"""

@router.patch("/password")
def change_password(
    data: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_member),
):
    # 1) 현재 비밀번호 확인
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    # 2) 새 비밀번호 확인
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    # 3) 새 비밀번호가 기존과 같은지 방지
    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")

    try:
        user.password_hash = get_password_hash(data.new_password)
        user.refresh_token_version += 1
        db.commit()
        db.refresh(user)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {type(e).__name__}")

    # refresh 쿠키 삭제 (비밀번호 바꿨으면 보통 다시 로그인 시킴)
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )

    return {
        "data": {
            "status": "password_updated",
        }
    }
