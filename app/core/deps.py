from typing import Generator
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user import Role

# Swagger Authorize에서 "Bearer 토큰" 입력받는 스키마
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = cred.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # access 토큰만 허용 (refresh 토큰 차단)
        if payload.get("type") and payload.get("type") != "access":
            raise JWTError()

        sub = payload.get("sub")
        if not sub:
            raise JWTError()

        # User.id가 UUID라서 변환
        user_id = uuid.UUID(sub)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

ROLE_LEVEL = {
    Role.GUEST: 0,
    Role.MEMBER: 1,
    Role.ADMIN: 2,
    Role.SUPERADMIN: 3,
}

def require_min_role(min_role: Role):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVEL[current_user.role] < ROLE_LEVEL[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role >= {min_role}",
            )
        return current_user
    return _checker

get_current_member = require_min_role(Role.MEMBER)
get_current_admin = require_min_role(Role.ADMIN)
get_current_superadmin = require_min_role(Role.SUPERADMIN)