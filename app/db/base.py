"""
base.py

SQLAlchemy ORM Base 정의 파일.

이 파일은 모든 SQLAlchemy 모델이 상속받는
공통 Base 클래스를 정의한다.

모든 모델(User, DuesCharge, DuesPayment 등)은
이 Base를 기준으로 테이블 메타데이터가 관리되며,
Alembic 마이그레이션 또한 이 Base를 기준으로 동작한다.

설계 원칙:
- Base 정의는 단일 파일에서만 관리
- 모델 간 순환 참조 방지
- Alembic autogenerate 안정성 확보

관련 파일:
- app.models.*            : 모든 ORM 모델
- alembic/env.py          : 마이그레이션 메타데이터 로드

"""

from sqlalchemy.orm import declarative_base

# 모든 ORM 모델이 상속받는 Base 클래스
Base = declarative_base()
