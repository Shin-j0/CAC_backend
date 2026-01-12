from pydantic import BaseModel, ConfigDict
from uuid import UUID
from app.models.user import Role

class RoleUpdate(BaseModel):
    role: Role

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: Role
    student_id: str
    phone: str
    grade: int

    model_config = ConfigDict(from_attributes=True)
