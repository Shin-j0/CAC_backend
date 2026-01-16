"""
security.py

비밀번호 해싱 및 JWT 토큰 생성/검증을 담당하는 보안 유틸리티 모음.

이 파일은 인증(auth) 로직에서 사용하는
저수준(low-level) 보안 기능만을 제공하며,
라우터나 비즈니스 로직은 포함하지 않는다.

주요 기능:
- 비밀번호 해싱 및 검증 (bcrypt)
- JWT Access Token 생성
- JWT Refresh Token 생성
- Refresh Token 디코딩 및 검증

설계 원칙:
- Access Token과 Refresh Token을 명확히 분리
- 토큰 생성 로직을 공통 함수로 통합하여 중복 제거
- Refresh Token에 version(rtv)을 포함하여 강제 로그아웃/토큰 무효화 지원
- 시간 기반(exp) 만료는 UTC 기준으로 처리

관련 파일:
- app.core.config        : JWT 시크릿 키 및 만료 설정
- app.core.deps          : 토큰을 실제로 검증하는 인증 의존성
- app.routers.auth       : 로그인 / 재발급 API

"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Tuple

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


# bcrypt 기반 비밀번호 해싱 컨텍스트
# deprecated="auto"로 향후 알고리즘 교체 가능하도록 설정

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


"""
비밀번호 해싱 함수

- 평문 비밀번호를 bcrypt 해시로 변환
- DB에는 해시 값만 저장

"""

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


"""
비밀번호 검증 함수

- 사용자가 입력한 평문 비밀번호와
  DB에 저장된 해시 값을 비교

"""

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


"""
JWT 토큰 생성 내부 공통 함수

- Access / Refresh 토큰 생성 로직을 공통화
- subject(sub): 사용자 식별자(user_id)
- token_type: access 또는 refresh
- exp: 만료 시각 (UTC timestamp)
- extra: Refresh Token의 rtv(version) 등 추가 정보

"""

def _create_token(*, subject: str, token_type: Literal["access", "refresh"],
                  expires_delta: timedelta, secret: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": int(expire.timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)


"""
Access Token 생성 함수

- API 요청 인증에 사용
- 비교적 짧은 만료 시간 사용
- Authorization Header(Bearer)에 담겨 전달됨

"""

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        secret=settings.SECRET_KEY,
    )


"""
Refresh Token 생성 함수

- Access Token 재발급에 사용
- 비교적 긴 만료 시간 사용
- refresh_token_version(rtv)을 포함하여
  서버 측에서 토큰 무효화 가능

"""

def create_refresh_token(subject: str, refresh_token_version: int, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        secret=settings.REFRESH_SECRET_KEY,
        extra={"rtv": refresh_token_version},
    )


"""
Refresh Token 디코딩 및 검증 함수

- Refresh Token의 유효성 검증
- 토큰 타입(refresh) 확인
- subject(user_id)와 rtv(version) 추출
- 유효하지 않을 경우 JWTError 발생

"""

def decode_refresh_token(token: str) -> tuple[str, int]:
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        sub = payload["sub"]
        rtv = int(payload.get("rtv", -1))
        return sub, rtv
    except JWTError as e:
        raise e

