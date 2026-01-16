"""
user.py

사용자(User) 및 권한(Role) 모델 정의 파일.

이 파일은 동아리 회원의 기본 정보와
권한(Role), 탈퇴 상태(Soft Delete), 인증 관련 정보를 관리한다.

모든 인증, 권한, 회비, 관리자 기능의 기준이 되는 핵심 모델이다.

"""

import uuid
import datetime
from enum import Enum

from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base



"""
사용자 권한(Role) 정의

- GUEST       : 가입 후 승인 대기 상태
- MEMBER      : 일반 회원
- ADMIN       : 관리자
- SUPERADMIN  : 최고 관리자
- DELETED     : 탈퇴(삭제) 처리된 사용자

"""

class Role(str, Enum):
    GUEST = "GUEST"
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"
    DELETED = "DELETED"



"""
사용자(User) 모델

- email / student_id 는 고유 식별자
- role을 통해 접근 권한 제어
- is_deleted / deleted_at 으로 Soft Delete 지원
- refresh_token_version 으로 강제 로그아웃 및 토큰 무효화 지원

"""

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    student_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)

    grade: Mapped[int] = mapped_column(Integer, nullable=False)

    role: Mapped[Role] = mapped_column(default=Role.GUEST)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
