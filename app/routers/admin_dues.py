from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.deps import get_db, get_current_admin
from app.models.user import User
from app.models.dues import DuesCharge, DuesPayment
from app.services.dues import validate_period, create_charge, record_payment, admin_status_for_period
from app.schemas.dues import (
    ChargeCreateRequest,
    ChargeResponse,
    PaymentCreateRequest,
    PaymentResponse,
    AdminDuesUserStatus,
)

router = APIRouter(prefix="/admin/dues", tags=["admin-dues"])

# 관리자 전용 회비 청구/납부 관리 엔드포인트
@router.post("/charges", response_model=ChargeResponse)
def create_dues_charge(
    body: ChargeCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        charge = create_charge(
            db,
            period=body.period,
            amount=body.amount,
            created_by=admin.id,
        )
        db.commit()
        db.refresh(charge)
        return charge
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        raise



# 목록 조회 엔드포인트
@router.get("/charges", response_model=list[ChargeResponse])
def list_dues_charges(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return db.scalars(select(DuesCharge).order_by(desc(DuesCharge.period))).all()

# 납부 기록 생성 엔드포인트
@router.post("/payments", response_model=PaymentResponse)
def create_dues_payment(
    body: PaymentCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        payment = record_payment(
            db,
            user_id=body.user_id,
            period=body.period,
            amount=body.amount,
            method=body.method,
            memo=body.memo,
            created_by=admin.id,
        )
        db.commit()
        db.refresh(payment)
        return payment
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        raise


# 월별 납부 현황 조회 엔드포인트
@router.get("/status", response_model=list[AdminDuesUserStatus])
def status_for_period(
    period: str = Query(..., description="예: 2026-01"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        validate_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    charge, rows = admin_status_for_period(db, period=period)
    if not charge:
        return []

    return [
        AdminDuesUserStatus(
            user_id=r["user"].id,
            name=r["user"].name,
            student_id=r["user"].student_id,
            amount_due=r["amount_due"],
            paid_amount=r["paid_amount"],
            status=r["status"],
        )
        for r in rows
    ]
