import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DuesCharge(Base):
    """월(또는 분기) 회비 '청구' 레코드.

    period: 'YYYY-MM' 형태 권장 (예: '2026-01')
    """

    __tablename__ = "dues_charges"
    __table_args__ = (
        UniqueConstraint("period", name="uq_dues_charges_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class DuesPayment(Base):
    """회비 '납부' 레코드.

    - charge_id: 어떤 청구(period)에 대한 납부인지
    - amount: 부분 납부/추가 납부를 지원하기 위해 합산 가능하도록 int로 유지
    """

    __tablename__ = "dues_payments"
    __table_args__ = (
        Index("ix_dues_payments_user_id", "user_id"),
        Index("ix_dues_payments_charge_id", "charge_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    charge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dues_charges.id"), nullable=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(20), default="TRANSFER", nullable=False)  # CASH/TRANSFER/ETC
    memo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
