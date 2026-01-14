# tests/helpers.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User, Role
from app.core.security import get_password_hash


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_admin_in_db(db: Session, *, email: str, password: str) -> User:
    admin = User(
        email=email,
        password_hash=get_password_hash(password),
        name="ADMIN",
        student_id=f"ADMIN-{uuid.uuid4().hex[:8]}",
        phone="010-0000-0000",
        grade=4,
        role=Role.ADMIN,
        is_deleted=False,
        deleted_at=None,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def setup_admin_and_member(client, db: Session):
    """
    ADMIN 토큰 + 승인된 MEMBER(user_id, token, student_id) 세팅
    """
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    admin_password = "AdminPassw0rd!"
    create_admin_in_db(db, email=admin_email, password=admin_password)

    admin_login = client.post("/auth/login", json={"email": admin_email, "password": admin_password})
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    user_email = f"user_{uuid.uuid4().hex[:6]}@test.com"
    user_password = "UserPassw0rd!"
    user_student_id = f"2022{uuid.uuid4().hex[:4]}"

    reg = client.post(
        "/auth/register",
        json={
            "email": user_email,
            "password": user_password,
            "name": "테스트유저",
            "student_id": user_student_id,
            "phone": "010-1234-5678",
            "grade": 2,
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["id"]

    approve = client.post(
        f"/admin/guest/{user_id}/approve",
        headers=auth_header(admin_token),
    )
    assert approve.status_code == 200, approve.text

    user_login = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert user_login.status_code == 200, user_login.text
    user_token = user_login.json()["access_token"]

    return {
        "admin_email": admin_email,
        "admin_password": admin_password,
        "admin_token": admin_token,
        "user_email": user_email,
        "user_password": user_password,
        "user_student_id": user_student_id,
        "user_id": user_id,
        "user_token": user_token,
    }


def get_user(db: Session, user_id: str) -> User:
    return db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
