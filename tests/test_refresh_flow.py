# tests/test_refresh_flow.py
import uuid
from tests.helpers import auth_header, create_admin_in_db


def test_refresh_token_rotation_and_revocation(client, db_session):
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    admin_password = "AdminPassw0rd!"
    create_admin_in_db(db_session, email=admin_email, password=admin_password)

    admin_login = client.post("/auth/login", json={"email": admin_email, "password": admin_password})
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    user_email = f"user_{uuid.uuid4().hex[:6]}@test.com"
    user_password = "UserPassw0rd!"
    user_student_id = f"2022{uuid.uuid4().hex[:4]}"

    reg = client.post(
        "/auth/register",
        json={"email": user_email, "password": user_password, "name": "리프레시테스트유저", "student_id": user_student_id, "phone": "010-7777-8888", "grade": 2},
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["id"]

    approve = client.post(f"/admin/guest/{user_id}/approve", headers=auth_header(admin_token))
    assert approve.status_code == 200, approve.text

    login = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert login.status_code == 200, login.text
    access1 = login.json()["access_token"]
    assert access1
    assert "refresh_token" in client.cookies
    refresh1 = client.cookies.get("refresh_token")
    assert refresh1

    r1 = client.post("/auth/refresh")
    assert r1.status_code == 200, r1.text
    access2 = r1.json()["access_token"]
    assert access2

    refresh2 = client.cookies.get("refresh_token")
    assert refresh2 and refresh2 != refresh1

    client.cookies.set("refresh_token", refresh1)
    r_old = client.post("/auth/refresh")
    assert r_old.status_code == 401
    assert r_old.json()["detail"] == "Refresh token revoked"

    client.cookies.set("refresh_token", refresh2)
    logout = client.post("/auth/logout", headers=auth_header(access2))
    assert logout.status_code == 204
