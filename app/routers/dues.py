from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.deps import get_db, get_current_member
from app.models.user import User
from app.models.dues import DuesCharge, DuesPayment
from app.services.dues import validate_period, sum_paid_for_charge, arrears_total
from app.schemas.dues import MyDuesStatusResponse, PaymentResponse

router = APIRouter(prefix="/dues", tags=["dues"])

# 회원 전용 회비 조회/납부 관리 엔드포인트
@router.get("/me", response_model=MyDuesStatusResponse)
def my_dues_status(
    period: str | None = Query(default=None, description="예: 2026-01"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member),
):
    # period 미지정이면 가장 최신 period(문자열 정렬 기준) 사용
    if period:
        try:
            validate_period(period)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        charge = db.scalar(select(DuesCharge).where(DuesCharge.period == period))
    else:
        charge = db.scalar(select(DuesCharge).order_by(desc(DuesCharge.period)))

    if not charge:
        return MyDuesStatusResponse(current_period=None, current_amount=0, paid_amount=0, status="NO_CHARGE", arrears_total=0)

    paid = sum_paid_for_charge(db, user_id=current_user.id, charge_id=charge.id)
    if paid <= 0:
        status = "UNPAID"
    elif paid < charge.amount:
        status = "PARTIAL"
    else:
        status = "PAID"

    arrears = arrears_total(db, user_id=current_user.id)

    return MyDuesStatusResponse(
        current_period=charge.period,
        current_amount=charge.amount,
        paid_amount=paid,
        status=status,
        arrears_total=arrears,
    )

# 납부 내역 조회 엔드포인트
@router.get("/me/payments", response_model=list[PaymentResponse])
def my_payments(
    period: str | None = Query(default=None, description="예: 2026-01"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member),
):
    if period:
        try:
            validate_period(period)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        charge = db.scalar(select(DuesCharge).where(DuesCharge.period == period))
        if not charge:
            return []

        payments = db.scalars(
            select(DuesPayment)
            .where(DuesPayment.user_id == current_user.id)
            .where(DuesPayment.charge_id == charge.id)
            .order_by(desc(DuesPayment.created_at))
        ).all()
    else:
        payments = db.scalars(
            select(DuesPayment)
            .where(DuesPayment.user_id == current_user.id)
            .order_by(desc(DuesPayment.created_at))
        ).all()

    return payments
