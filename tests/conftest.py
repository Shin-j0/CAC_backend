"""





pytest 공통 fixture 설정 파일.
- 테스트 DB 엔진/세션을 매 테스트마다 초기화(drop/create)하고,
  FastAPI get_db 의존성을 테스트 DB 세션으로 override한다.




"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.deps import get_db
from app.db.base import Base


from app.models.user import User  # noqa: F401
from app.models.dues import DuesCharge, DuesPayment  # noqa: F401
from app.models.admin_log import AdminActionLog  # noqa: F401


@pytest.fixture(scope="function")
def test_engine():
    """테스트마다 DB 초기화(drop/create)"""
    if not settings.TEST_DATABASE_URL:
        raise RuntimeError("TEST_DATABASE_URL is not set. Check your .env")

    engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    """FastAPI get_db 의존성을 테스트 DB 세션으로 override"""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
