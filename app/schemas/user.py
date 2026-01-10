from pydantic import BaseModel
from enum import Enum
from uuid import UUID


# 🔹 Role Enum (models와 동일한 값)
class Role(str, Enum):
    GUEST = "GUEST"
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"


# 🔹 관리자 role 변경 요청용
class RoleUpdate(BaseModel):
    role: Role


# 🔹 유저 응답용 (필요한 필드만)
class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: Role
    student_id: str
    phone: str
    grade: int

    class Config:
        from_attributes = True  # SQLAlchemy → Pydantic 변환
