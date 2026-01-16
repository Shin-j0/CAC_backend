"""

admin_log.py

관리자(Admin) 행위 기록(Audit Log) 모델 정의 파일.

이 파일은 관리자에 의해 수행된 주요 관리 행위
(회원 승인, 거절, 삭제, 권한 변경 등)를
DB에 영구적으로 기록하기 위한 로그 테이블을 정의한다.

운영 중 발생할 수 있는 문제 추적,
권한 오남용 방지, 감사(Audit) 목적을 위한 핵심 모델이다.

설계 원칙:
- 실제 데이터 변경과 로그 기록을 분리
- 로그 데이터는 수정/삭제하지 않는 것을 전제로 설계
- actor(행위자)와 target(대상 사용자)을 명확히 구분

"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base



#  관리자 행위 유형 Enum

class AdminAction(str, Enum):
    APPROVE_USER = "APPROVE_USER"
    REJECT_USER = "REJECT_USER"
    DELETE_USER = "DELETE_USER"
    SET_ROLE = "SET_ROLE"


"""
관리자 행위 로그 모델

- actor_id       : 행위를 수행한 관리자 ID
- target_user_id : 행위 대상 사용자 ID (없을 수 있음)
- action         : 수행된 관리자 행위 유형
- before_role    : 변경 전 권한
- after_role     : 변경 후 권한
- ip             : 요청 IP 주소
- user_agent     : 요청 User-Agent
- created_at     : 행위 발생 시각 (UTC)

"""

class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    action: Mapped[AdminAction] = mapped_column(SAEnum(AdminAction, name="admin_action"), nullable=False)

    before_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    after_role: Mapped[str | None] = mapped_column(String(20), nullable=True)

    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
