"""
dues.py

회원(Member) 전용 회비 조회 API 모음.

이 파일은 로그인한 일반 회원이
본인의 회비 납부 상태와 납부 내역을 조회하기 위한 기능을 담당한다.
관리자용 회비 관리 기능과 분리하여,
권한 경계와 책임을 명확히 하기 위한 구조이다.

주요 기능:
- 본인 기준 월별 회비 납부 상태 조회
- 본인 기준 회비 납부 내역 조회

설계 원칙:
- MEMBER 이상 권한만 접근 가능
- 모든 데이터는 "본인 기준"으로만 조회
- 회비 계산 로직은 service 계층(app.services.dues)에 위임
- 회비 미청구 기간도 안전하게 처리 (NO_CHARGE 상태 반환)

관련 파일:
- app.services.dues        : 회비 계산 및 누적 미납 로직
- app.models.dues          : 회비 청구 / 납부 모델
- app.schemas.dues         : 회원용 회비 응답 스키마

"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.deps import get_db, get_current_member
from app.models.user import User
from app.models.dues import DuesCharge, DuesPayment
from app.services.dues import validate_period, sum_paid_for_charge, arrears_total
from app.schemas.dues import MyDuesStatusResponse, PaymentResponse

router = APIRouter(prefix="/dues", tags=["dues"])

"""
회원 본인 회비 납부 현황 조회 API

- 로그인한 회원 본인의 회비 상태만 조회
- period 미지정 시 가장 최신 회비 청구 기준으로 조회
- 납부 상태를 PAID / PARTIAL / UNPAID / NO_CHARGE 로 계산
- 누적 미납 금액(arrears_total)을 함께 반환

"""
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

"""
회원 본인 회비 납부 내역 조회 API

- 로그인한 회원 본인의 납부 기록만 조회
- period 지정 시 해당 월의 납부 내역만 반환
- period 미지정 시 전체 납부 내역을 최신순으로 반환

"""
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
