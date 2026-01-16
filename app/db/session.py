"""
session.py

데이터베이스 엔진 및 세션(Session) 관리 파일.

이 파일은 SQLAlchemy Engine과 SessionLocal을 생성하여
애플리케이션 전반에서 공통으로 사용하는 DB 연결을 관리한다.

FastAPI 의존성(get_db)을 통해
요청 단위로 세션을 생성/종료하는 구조를 지원한다.

설계 원칙:
- DB 연결 설정은 한 곳에서만 정의
- 세션 생성/종료 책임을 명확히 분리
- pool_pre_ping=True로 유휴 연결 오류 방지

관련 파일:
- app.core.config        : DATABASE_URL 설정
- app.core.deps          : get_db 의존성

"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# SQLAlchemy Engine 생성
# pool_pre_ping=True:
#   장시간 idle 후 끊어진 DB 커넥션을 자동으로 감지/재연결
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# 요청 단위로 사용할 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
