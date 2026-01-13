import uuid
from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel, Field, ConfigDict


PeriodStr = str  # 'YYYY-MM' (검증은 라우터에서 간단히 체크)


class ChargeCreateRequest(BaseModel):
    period: PeriodStr = Field(..., examples=["2026-01"])
    amount: int = Field(..., ge=0, examples=[10000])


class ChargeResponse(BaseModel):
    id: uuid.UUID
    period: PeriodStr
    amount: int
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


PaymentMethod = Literal["CASH", "TRANSFER", "ETC"]


class PaymentCreateRequest(BaseModel):
    user_id: uuid.UUID
    period: PeriodStr = Field(..., examples=["2026-01"])
    amount: int = Field(..., gt=0, examples=[10000])
    method: PaymentMethod = "TRANSFER"
    memo: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    charge_id: uuid.UUID
    amount: int
    method: str
    memo: Optional[str]
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MyDuesStatusResponse(BaseModel):
    current_period: Optional[PeriodStr]
    current_amount: int = 0
    paid_amount: int = 0
    status: Literal["PAID", "PARTIAL", "UNPAID", "NO_CHARGE"] = "NO_CHARGE"
    arrears_total: int = 0  # 누적 미납


class AdminDuesUserStatus(BaseModel):
    user_id: uuid.UUID
    name: str
    student_id: str
    amount_due: int
    paid_amount: int
    status: Literal["PAID", "PARTIAL", "UNPAID", "NO_CHARGE"]
