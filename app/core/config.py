"""
config.py

애플리케이션 전역 설정(Configuration) 관리 파일.

이 파일은 .env 환경 변수들을 Pydantic BaseSettings를 통해 로드하여
애플리케이션 전반에서 공통으로 사용하는 설정 값을 제공한다.

주요 설정 항목:
- 데이터베이스 연결 정보
- JWT 인증 관련 시크릿 및 만료 정책
- 쿠키 보안 옵션
- CORS 허용 도메인 목록

설계 원칙:
- 모든 환경 변수는 이 파일을 통해서만 접근
- 로컬 / 테스트 / 운영 환경을 .env로 분리하여 관리
- 설정 값은 런타임 중 변경되지 않는 불변 객체로 취급

관련 파일:
- app.main               : CORS 및 앱 초기화 시 설정 사용
- app.core.security      : JWT 시크릿 / 만료 설정 사용
- app.db.session         : DATABASE_URL 사용

"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# .env 파일에 정의된 환경 변수를 로드하는 설정 클래스
# extra="ignore" 옵션으로 정의되지 않은 환경 변수는 무시
#.env 파일에 들어있는 정보 불러와서 사용 -> 시크릿 키/ superadmin 계정 등등
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
    # - COOKIE_SECURE: HTTPS 환경에서만 True 권장
    # - COOKIE_SAMESITE: CSRF 완화를 위해 "lax" 기본값

    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None

    # CORS 허용 도메인 (프론트엔드 주소)
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

# 애플리케이션 전역에서 import하여 사용하는 Settings 인스턴스
# 실행 시 한 번만 생성됨
settings = Settings()
