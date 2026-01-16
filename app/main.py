"""
main.py

FastAPI 애플리케이션 진입점(Entry Point).

이 파일은 서버 실행 시 가장 먼저 로드되며,
애플리케이션 전반의 설정과 라우터 등록을 담당한다.

주요 역할:
- FastAPI 앱 인스턴스 생성
- CORS 미들웨어 설정
- 각 도메인별 라우터(auth, users, admin, dues 등) 등록
- 헬스 체크 및 DB 연결 상태 확인용 엔드포인트 제공

설계 원칙:
- 비즈니스 로직은 포함하지 않고 설정/조립 역할만 수행
- 실제 기능은 routers / services 계층에 위임
- 운영 환경에서도 안전하게 상태 확인 가능하도록 health/db-ping 제공

관련 파일:
- app.core.config        : 환경 변수 및 설정 로드
- app.core.deps          : DB 세션 의존성
- app.routers.*          : 기능별 API 라우터

"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.deps import get_db
from app.routers import auth, users, admin, dues, admin_dues

app = FastAPI(title="Club Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(dues.router)
app.include_router(admin_dues.router)

"""
서버 헬스 체크 엔드포인트

- 애플리케이션 프로세스가 정상 동작 중인지 확인
- 로드밸런서 / 배포 환경에서 서버 상태 확인 용도

"""
@app.get("/health")
def health():
    return {"status": "ok"}

"""
데이터베이스 연결 상태 확인 엔드포인트

- 간단한 SELECT 1 쿼리를 통해 DB 연결 여부 확인
- 서버는 살아 있으나 DB가 죽은 상황을 분리해서 감지 가능

"""
@app.get("/db-ping")
def db_ping(db: Session = Depends(get_db)):
    value = db.execute(text("SELECT 1")).scalar_one()
    return {"db": "ok", "value": value}
