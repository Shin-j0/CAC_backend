from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    SECRET_KEY: str
    REFRESH_SECRET_KEY: str  # ✅ 추가 (access랑 분리 추천)
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # 쿠키/배포 옵션
    COOKIE_SECURE: bool = False          # 로컬은 False, HTTPS 운영은 True
    COOKIE_SAMESITE: str = "lax"         # "lax" 추천
    COOKIE_DOMAIN: str | None = None     # 필요시만

    # CORS(프론트 주소들)
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

settings = Settings()
