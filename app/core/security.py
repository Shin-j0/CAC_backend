from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Tuple

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


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



def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        secret=settings.SECRET_KEY,
    )


def create_refresh_token(subject: str, refresh_token_version: int, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        secret=settings.REFRESH_SECRET_KEY,
        extra={"rtv": refresh_token_version},
    )



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

