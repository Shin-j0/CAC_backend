"""
deps.py

FastAPI 의존성(Dependencies) 모음.

이 파일은 인증(Authentication), 권한(Role) 검증,
그리고 데이터베이스 세션 관리와 관련된 공통 의존성을 제공한다.

라우터에서는 이 파일의 함수들을 Depends()로 주입받아 사용하며,
이를 통해 인증/권한 로직을 중앙에서 일관되게 관리한다.

주요 기능:
- DB 세션 생성 및 종료 관리
- JWT Access Token 기반 현재 사용자 조회
- 역할(Role) 최소 권한 검증 (MEMBER / ADMIN / SUPERADMIN)

설계 원칙:
- 인증/권한 로직을 라우터에서 분리
- 모든 API에서 동일한 기준으로 권한 체크
- Refresh Token은 deps에서 허용하지 않음 (Access Token 전용)

관련 파일:
- app.core.security      : JWT 생성 및 검증
- app.models.user        : User / Role 모델
- app.core.config        : JWT 시크릿 및 알고리즘 설정

"""

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

"""
데이터베이스 세션 의존성

- 요청 단위로 SQLAlchemy Session 생성
- 요청 종료 시 세션 자동 close
- 모든 DB 접근 API에서 공통으로 사용

"""

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
현재 로그인 사용자 조회 (Access Token 기반)

- Authorization 헤더의 Bearer 토큰을 검증
- Access Token만 허용 (Refresh Token 차단)
- 토큰이 유효하지 않거나 사용자가 없으면 401 반환

"""

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


# 역할(Role)별 권한 레벨 정의
# 숫자가 클수록 높은 권한

ROLE_LEVEL = {
    Role.DELETED: -1,
    Role.GUEST: 0,
    Role.MEMBER: 1,
    Role.ADMIN: 2,
    Role.SUPERADMIN: 3,
}



"""
최소 권한(Role) 요구 의존성 생성기

- 지정한 최소 권한 이상을 가진 사용자만 통과
- 미달 시 403 Forbidden 반환
- get_current_user 결과를 그대로 반환

"""

def require_min_role(min_role: Role):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVEL[current_user.role] < ROLE_LEVEL[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role >= {min_role}",
            )
        return current_user
    return _checker

"""
권한별 의존성 단축 정의

- get_current_member     : MEMBER 이상
- get_current_admin      : ADMIN 이상
- get_current_superadmin : SUPERADMIN 전용
"""
get_current_member = require_min_role(Role.MEMBER)
get_current_admin = require_min_role(Role.ADMIN)
get_current_superadmin = require_min_role(Role.SUPERADMIN)
