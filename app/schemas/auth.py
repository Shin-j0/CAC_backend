import uuid
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    name: str
    student_id: str
    phone: str
    grade: int

class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DeleteMeRequest(BaseModel):
    password: str

class EditProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    grade: int | None = None
    current_password: str = Field(..., min_length=1)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)