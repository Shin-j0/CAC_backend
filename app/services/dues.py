"""
services/dues.py

회비(Dues) 도메인의 비즈니스 로직 모음.

이 파일은 회비 청구, 납부, 정산, 상태 계산 등
회비 시스템의 핵심 규칙을 담당한다.

라우터는 이 파일의 함수를 호출하여
검증/계산 결과를 받아 응답만 처리한다.

설계 원칙:
- 회비 관련 모든 규칙을 한 곳에 집중
- period 형식 검증을 공통 함수로 제공
- 금액 계산은 항상 DB 기준으로 수행

관련 파일:
- app.models.dues        : DuesCharge / DuesPayment 모델
- app.models.user        : User / Role 모델
- app.routers.admin_dues : 관리자 회비 API
- app.routers.dues       : 회원 회비 조회 API

"""

import re
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.dues import DuesCharge, DuesPayment
from app.models.user import User, Role


_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


"""
회비 period 형식 검증

- 'YYYY-MM' 형식만 허용
- 월(month)은 01 ~ 12 범위만 허용
- 형식이 잘못되면 ValueError 발생

"""

def validate_period(period: str) -> None:
    if not _PERIOD_RE.match(period):
        raise ValueError("period must be in 'YYYY-MM' format")
    try:
        month = int(period.split("-")[1])
    except Exception:
        raise ValueError("period must be in 'YYYY-MM' format")

    if month < 1 or month > 12:
        raise ValueError("month must be between 01 and 12")


"""
특정 period의 회비 청구 조회

- 존재하지 않으면 None 반환

"""

def get_charge_by_period(db: Session, period: str) -> DuesCharge | None:
    return db.scalar(select(DuesCharge).where(DuesCharge.period == period))

"""
회비 청구 생성

- period 중복 생성 불가
- 생성 즉시 DB flush 수행

"""
def create_charge(db: Session, *, period: str, amount: int, created_by: uuid.UUID) -> DuesCharge:
    validate_period(period)

    existing = get_charge_by_period(db, period)
    if existing:
        raise ValueError("charge for that period already exists")

    charge = DuesCharge(period=period, amount=amount, created_by=created_by)

    db.add(charge)
    db.flush()
    return charge


"""
회비 납부 기록 생성

- 해당 period에 대한 청구가 존재해야 함
- user 존재 여부 검증
- 부분 납부 / 추가 납부 허용

"""
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


# 특정 회비 청구에 대해 사용자가 납부한 총 금액 계산
def sum_paid_for_charge(db: Session, *, user_id: uuid.UUID, charge_id: uuid.UUID) -> int:
    paid = db.scalar(
        select(func.coalesce(func.sum(DuesPayment.amount), 0))
        .where(DuesPayment.user_id == user_id)
        .where(DuesPayment.charge_id == charge_id)
    )
    return int(paid or 0)



"""
사용자의 전체 회비 누적 미납 금액 계산

- 모든 회비 청구 기준으로 계산
- (청구 금액 - 납부 금액)의 합

"""

def arrears_total(db: Session, *, user_id: uuid.UUID) -> int:
    # 모든 청구에 대해 paid < amount 인 부족분 합산
    charges = db.scalars(select(DuesCharge)).all()
    total = 0
    for c in charges:
        paid = sum_paid_for_charge(db, user_id=user_id, charge_id=c.id)
        if paid < c.amount:
            total += (c.amount - paid)
    return total


"""
관리자용 월별 회비 납부 현황 계산

- MEMBER / ADMIN 대상 - superadmin은 제외
- PAID / PARTIAL / UNPAID 상태 계산
- 청구가 없으면 (None, []) 반환

"""

def admin_status_for_period(db: Session, *, period: str):
    validate_period(period)
    charge = get_charge_by_period(db, period)
    if not charge:
        return None, []

    members = db.scalars(select(User).where(User.role.in_([Role.MEMBER, Role.ADMIN]))).all()

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

