"""
admin_dues.py

관리자 전용 회비 관리 API 모음.

이 파일은 동아리 회비(dues)에 대한 "관리자 권한" 기능만을 담당한다.
일반 회원용 회비 조회 API와 역할을 분리하여,
권한 관리와 비즈니스 책임을 명확히 하기 위한 구조이다.

주요 기능:
- 월별 회비 청구 생성 및 목록 조회
- 회원별 회비 납부 기록 생성
- 월별 회비 납부 현황 조회 (PAID / PARTIAL / UNPAID)
- 관리자용 CSV / Excel(xlsx) 데이터 내보내기

설계 원칙:
- 모든 엔드포인트는 관리자 권한(get_current_admin)을 요구
- 비즈니스 로직은 service 계층(app.services.dues)에 위임
- 이 라우터는 요청/응답 처리 및 권한 검증에만 집중
- 회비 데이터는 Soft Delete 사용자(is_deleted=True)를 기본적으로 제외

관련 파일:
- app.services.dues        : 회비 계산 및 검증 로직
- app.models.dues          : 회비 관련 DB 모델
- app.schemas.dues         : 요청/응답 스키마 정의
"""

import csv
import io
from starlette.responses import StreamingResponse, Response
from openpyxl import Workbook

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


"""
관리자 전용 회비 청구 생성 API

- 특정 period(YYYY-MM)에 대한 회비 청구를 생성
- 동일 period에 대한 중복 청구는 허용하지 않음
- 실제 비즈니스 검증 로직은 service(create_charge)에서 처리

"""
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


"""
관리자 전용 회비 청구 목록 조회 API

- 생성된 모든 회비 청구를 period 기준 내림차순으로 반환
- 최신 회비 청구가 상단에 오도록 정렬

"""
@router.get("/charges", response_model=list[ChargeResponse])
def list_dues_charges(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return db.scalars(select(DuesCharge).order_by(desc(DuesCharge.period))).all()

"""
관리자 전용 회비 납부 기록 생성 API

- 특정 사용자(user_id)에 대한 회비 납부 내역을 추가
- 부분 납부 / 추가 납부를 허용
- 청구가 존재하지 않는 period에 대해서는 납부 불가

"""
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


"""
관리자 전용 월별 회비 납부 현황 조회 API

- 지정한 period(YYYY-MM)의 회원별 납부 상태를 조회
- PAID / PARTIAL / UNPAID 상태로 계산하여 반환
- 해당 period의 회비 청구가 없으면 빈 리스트 반환

"""
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


"""
    관리자용 월별 회비 납부 현황 CSV 다운로드 API

    - 지정한 period(YYYY-MM)의 회원별 납부 상태를 CSV 파일로 반환
    - StreamingResponse를 사용해 대용량 데이터도 메모리 부담 없이 처리
    - UTF-8 BOM을 추가하여 Excel에서 한글이 깨지지 않도록 처리

"""
@router.get("/export")
def export_status_csv(
    period: str = Query(..., description="예: 2026-01"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        validate_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    charge, rows = admin_status_for_period(db, period=period)

    def generate():
        # Excel에서 UTF-8 CSV 한글 깨짐 방지를 위해 BOM(Byte Order Mark) 먼저 출력
        yield "\ufeff"

        output = io.StringIO()
        writer = csv.writer(output)

        # CSV 헤더 행
        writer.writerow(
            ["period", "name", "student_id", "status", "amount_due", "paid_amount"]
        )
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # charge 없으면 헤더만 내보내고 종료
        if not charge:
            return

        for r in rows:
            u = r["user"]
            writer.writerow(
                [period, u.name, u.student_id, r["status"], r["amount_due"], r["paid_amount"]]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"dues_status_{period}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        generate(),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


"""
관리자용 월별 회비 납부 내역 CSV 다운로드 API

- 특정 월(period)에 대한 모든 납부 기록을 CSV로 제공
- 납부 ID, 사용자 ID, 금액, 결제 수단, 메모 등 원본 데이터 포함
- BOM을 포함한 UTF-8 CSV로 Excel 호환성 보장

"""

@router.get("/payments/export")
def export_payments_csv(
    period: str = Query(..., description="예: 2026-01"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        validate_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    charge = db.scalar(select(DuesCharge).where(DuesCharge.period == period))

    def generate():
        # Excel에서 UTF-8 CSV 한글 깨짐 방지를 위해 BOM(Byte Order Mark) 먼저 출력
        yield "\ufeff"

        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(["period", "payment_id", "user_id", "amount", "method", "memo", "created_by", "created_at"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # 해당 월 청구가 없으면 헤더만
        if not charge:
            return

        payments = db.scalars(
            select(DuesPayment)
            .where(DuesPayment.charge_id == charge.id)
            .order_by(desc(DuesPayment.created_at))
        ).all()

        for p in payments:
            # CSV는 문자열 기반 포맷이므로 UUID / datetime은 문자열로 변환
            writer.writerow([
                period,
                str(p.id),
                str(p.user_id),
                p.amount,
                p.method,
                p.memo or "",
                str(p.created_by),
                p.created_at.isoformat() if p.created_at else "",
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"dues_payments_{period}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(generate(), media_type="text/csv; charset=utf-8", headers=headers)

# NOTE:
# - 회비 관련 비즈니스 로직은 service 계층에서 처리
# - 라우터는 요청/응답과 권한 검증에만 집중

"""
관리자용 월별 회비 납부 현황 Excel(xlsx) 다운로드 API

- CSV 대신 Excel 형식이 필요한 경우를 위한 엔드포인트
- openpyxl을 사용하여 XLSX 파일 생성
- 한글 깨짐 없이 바로 Excel에서 열 수 있음

"""

@router.get("/export.xlsx")
def export_status_xlsx(
    period: str = Query(..., description="예: 2026-01"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    try:
        validate_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    charge, rows = admin_status_for_period(db, period=period)

    wb = Workbook()
    ws = wb.active
    ws.title = "dues_status"

    # Excel 시트 헤더
    ws.append(["period", "name", "student_id", "status", "amount_due", "paid_amount"])

    # 데이터
    if charge:
        for r in rows:
            u = r["user"]
            ws.append([
                period,
                u.name,
                u.student_id,
                r["status"],
                r["amount_due"],
                r["paid_amount"],
            ])

    buf = io.BytesIO()
    wb.save(buf)
    data = buf.getvalue()

    # Content-Disposition 헤더를 통해 브라우저에서 파일 다운로드로 처리
    filename = f"dues_status_{period}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

# NOTE:
# CSV는 엑셀 호환성 문제로 BOM + UTF-8 스트리밍 방식 사용
# XLSX는 Excel에서 바로 열기 위한 대안 포맷
