import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse, DeleteMeRequest

from jose import JWTError, ExpiredSignatureError

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"

# 회원가입 엔드포인트
@router.post("/register", response_model=RegisterResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == data.email))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )   

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        name=data.name,
        student_id=data.student_id,
        phone=data.phone,
        grade=data.grade,
        role=Role.GUEST,
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}

# 로그인 엔드포인트
@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # guest는 로그인 불가
    if user.role == Role.GUEST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pending approval"
        )
    
    access = create_access_token(subject=str(user.id))
    refresh = create_refresh_token(subject=str(user.id))

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

    return TokenResponse(access_token=access)

# 토큰 재발급 엔드포인트
@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        user_id = decode_refresh_token(token)
        user_uuid = uuid.UUID(user_id)
    except (ExpiredSignatureError, JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # 유저 존재 확인(탈퇴/삭제 대응)
    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token(subject=str(user.id))

    # (선택/권장) refresh rotation: refresh도 새로 발급해서 쿠키 교체
    new_refresh = create_refresh_token(subject=str(user.id))
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

    return TokenResponse(access_token=new_access)

# 로그아웃 엔드포인트
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return Response(status_code=204)

# 회원(본인) 탈퇴 엔드포인트
@router.delete("/me")
def delete_me(
    data: DeleteMeRequest,
    response: Response,
    db: Session = Depends(get_db),
    member: User = Depends(get_current_member),
):
    if not verify_password(data.password, member.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    try:
        db.delete(member)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return {"message": "User deleted"}