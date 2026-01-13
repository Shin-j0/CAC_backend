import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.core.config import settings
from app.core.deps import get_db
from app.db.base import Base

# ✅ 모델 import (Base.metadata에 테이블 등록)
import app.models  # noqa: F401


TEST_DB_URL = getattr(settings, "TEST_DATABASE_URL", None) or os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set. Add it to .env or env var for tests.")

engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """테스트 전체 시작/종료 때만 스키마 생성/삭제"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """각 테스트마다 데이터 초기화 (테이블은 유지, row만 삭제)"""
    # FK 의존성 때문에 TRUNCATE ... CASCADE가 가장 깔끔함
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE users, admin_action_logs, dues_charges, dues_payments RESTART IDENTITY CASCADE;"))


@pytest.fixture()
def db():
    """테스트에서 직접 DB 조작할 때 쓰는 세션"""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client():
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
