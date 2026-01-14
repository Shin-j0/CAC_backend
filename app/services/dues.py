import re
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.dues import DuesCharge, DuesPayment
from app.models.user import User, Role


_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_period(period: str) -> None:
    if not _PERIOD_RE.match(period):
        raise ValueError("period must be in 'YYYY-MM' format")
    try:
        month = int(period.split("-")[1])
    except Exception:
        raise ValueError("period must be in 'YYYY-MM' format")

    if month < 1 or month > 12:
        raise ValueError("month must be between 01 and 12")



def get_charge_by_period(db: Session, period: str) -> DuesCharge | None:
    return db.scalar(select(DuesCharge).where(DuesCharge.period == period))


def create_charge(db: Session, *, period: str, amount: int, created_by: uuid.UUID) -> DuesCharge:
    validate_period(period)

    existing = get_charge_by_period(db, period)
    if existing:
        raise ValueError("charge for that period already exists")

    charge = DuesCharge(period=period, amount=amount, created_by=created_by)

    db.add(charge)
    db.flush()
    return charge


def record_payment(
    db: Session,
    *,
    user_id: uuid.UUID,
    period: str,
    amount: int,
    method: str,
    memo: str | None,
    created_by: uuid.UUID,
) -> DuesPayment:
    validate_period(period)
    charge = get_charge_by_period(db, period)
    if not charge:
        raise ValueError("charge not found for that period")

    # user 존재 검증 (MEMBER/ADMIN 포함)
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise ValueError("user not found")

    payment = DuesPayment(
        user_id=user_id,
        charge_id=charge.id,
        amount=amount,
        method=method,
        memo=memo,
        created_by=created_by,
    )
    db.add(payment)
    db.flush()
    return payment


def sum_paid_for_charge(db: Session, *, user_id: uuid.UUID, charge_id: uuid.UUID) -> int:
    paid = db.scalar(
        select(func.coalesce(func.sum(DuesPayment.amount), 0))
        .where(DuesPayment.user_id == user_id)
        .where(DuesPayment.charge_id == charge_id)
    )
    return int(paid or 0)


def arrears_total(db: Session, *, user_id: uuid.UUID) -> int:
    # 모든 청구에 대해 paid < amount 인 부족분 합산
    charges = db.scalars(select(DuesCharge)).all()
    total = 0
    for c in charges:
        paid = sum_paid_for_charge(db, user_id=user_id, charge_id=c.id)
        if paid < c.amount:
            total += (c.amount - paid)
    return total


def admin_status_for_period(db: Session, *, period: str):
    validate_period(period)
    charge = get_charge_by_period(db, period)
    if not charge:
        return None, []

    members = db.scalars(select(User).where(User.role.in_([Role.MEMBER, Role.ADMIN, Role.SUPERADMIN]))).all()

    rows = []
    for u in members:
        paid = sum_paid_for_charge(db, user_id=u.id, charge_id=charge.id)
        if paid <= 0:
            st = "UNPAID"
        elif paid < charge.amount:
            st = "PARTIAL"
        else:
            st = "PAID"
        rows.append({"user": u, "amount_due": charge.amount, "paid_amount": paid, "status": st})
    return charge, rows

