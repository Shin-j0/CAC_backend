"""





인증 기본 플로우 통합 테스트.
- 회원가입(GUEST) → 승인 전 로그인 차단 → 관리자 승인 → 로그인 성공,
  거절 후 재가입(복구) 흐름, 회원 탈퇴(멤버 OK / 관리자 금지)까지 검증한다.


"""

import uuid

from tests.helpers import auth_header, create_admin_in_db


def test_register_approve_login_flow(client, db_session):
    # ADMIN 토큰
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    admin_password = "AdminPassw0rd!"
    create_admin_in_db(db_session, email=admin_email, password=admin_password)

    admin_login = client.post("/auth/login", json={"email": admin_email, "password": admin_password})
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    # 회원가입(GUEST)
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

    # 승인 전 로그인 차단(403)
    pending_login = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert pending_login.status_code == 403
    assert pending_login.json()["detail"] == "Pending approval"

    # 승인
    approve = client.post(f"/admin/guest/{user_id}/approve", headers=auth_header(admin_token))
    assert approve.status_code == 200, approve.text
    assert approve.json()["data"]["after_role"] == "MEMBER"

    # 승인 후 로그인 OK
    ok_login = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert ok_login.status_code == 200, ok_login.text
    user_token = ok_login.json()["access_token"]

    # 보호 API
    profile = client.get("/users/profile", headers=auth_header(user_token))
    assert profile.status_code == 200, profile.text
    assert profile.json()["role"] == "MEMBER"


def test_register_reject_reregister_flow(client, db_session):
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
        json={
            "email": user_email,
            "password": user_password,
            "name": "거절테스트유저",
            "student_id": user_student_id,
            "phone": "010-9999-8888",
            "grade": 1,
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["id"]

    reject = client.post(f"/admin/guest/{user_id}/reject", headers=auth_header(admin_token))
    assert reject.status_code == 200, reject.text

    login_after_reject = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert login_after_reject.status_code == 401
    assert login_after_reject.json()["detail"] == "Invalid credentials"

    # 같은 이메일 재가입 -> 복구(GUEST)
    rereg = client.post(
        "/auth/register",
        json={
            "email": user_email,
            "password": user_password,
            "name": "복구된유저",
            "student_id": user_student_id,
            "phone": "010-0000-1111",
            "grade": 2,
        },
    )
    assert rereg.status_code == 200, rereg.text

    # 복구 후도 GUEST라 로그인 403
    login_after_rereg = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert login_after_rereg.status_code == 403
    assert login_after_rereg.json()["detail"] == "Pending approval"


def test_delete_me_member_ok_and_admin_forbidden(client, db_session):
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
        json={
            "email": user_email,
            "password": user_password,
            "name": "탈퇴테스트유저",
            "student_id": user_student_id,
            "phone": "010-1111-2222",
            "grade": 2,
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["id"]

    approve = client.post(f"/admin/guest/{user_id}/approve", headers=auth_header(admin_token))
    assert approve.status_code == 200, approve.text

    login = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert login.status_code == 200, login.text
    user_token = login.json()["access_token"]

    # ❗ delete는 TestClient 버전 이슈 때문에 request로
    delete_me = client.request("DELETE", "/auth/me", headers=auth_header(user_token), json={"password": user_password})
    assert delete_me.status_code == 200, delete_me.text

    login_after = client.post("/auth/login", json={"email": user_email, "password": user_password})
    assert login_after.status_code == 401

    delete_admin = client.request("DELETE", "/auth/me", headers=auth_header(admin_token), json={"password": admin_password})
    assert delete_admin.status_code == 403
