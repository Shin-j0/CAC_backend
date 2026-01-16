"""
services/admin.py

관리자 관련 비즈니스 로직(Service) 모음.

이 파일은 관리자 기능에서 공통으로 사용되는
순수 비즈니스 로직을 담당한다.
라우터에서는 이 파일의 함수를 호출하여
DB 조회/검증/정책 판단을 수행한다.

주요 기능:
- 현재 ADMIN 계정 수 계산
- 관리자 권한 변경/삭제 시 안전장치 제공

설계 원칙:
- HTTP / FastAPI 의존성 없음
- 트랜잭션 제어는 라우터에서 수행
- 관리자 정책(마지막 ADMIN 보호 등)을 중앙에서 관리

관련 파일:
- app.models.user        : User / Role 모델
- app.routers.admin      : 관리자 API

"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.user import User, Role


"""
현재 활성 ADMIN 계정 수를 반환

- Role.ADMIN 인 사용자만 집계
- 마지막 ADMIN 보호 로직에서 사용

"""

def count_admins(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.role == Role.ADMIN)
    ) or 0
