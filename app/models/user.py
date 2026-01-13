import uuid
import datetime
from enum import Enum

from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Role(str, Enum):
    GUEST = "GUEST"
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"
    DELETED = "DELETED"


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

    # ✅ role은 Enum 타입을 DB에 저장하려면 보통 sa.Enum(Role)로 지정하는 게 안전함
    # 지금은 기존 코드 유지(문제 없으면 OK). 만약 enum 컬럼 타입으로 확실히 하려면 말해줘.
    role: Mapped[Role] = mapped_column(default=Role.GUEST)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
