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