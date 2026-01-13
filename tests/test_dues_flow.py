import uuid
from sqlalchemy import select

from app.models.user import User, Role

PERIOD = "2026-01"


def _register(client, email, password, name="테스트", student_id="20260001"):
    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
        "student_id": student_id,
        "phone": "010-0000-0000",
        "grade": 1
    })
    assert r.status_code in (200, 201), r.text


def _login(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _set_role(db, email: str, role: Role):
    u = db.scalar(select(User).where(User.email == email))
    assert u is not None
    u.role = role
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_dues_member_cannot_access_when_guest(client, db):
    # 회원가입은 기본 GUEST
    email = "dues_guest@example.com"
    pw = "TestPassword123!"
    _register(client, email, pw, student_id="20261000")

    token = _login(client, email, pw)
    r = client.get("/dues/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, r.text  # MEMBER 전용


def test_dues_happy_path_admin_charge_and_payment(client, db):
    # 1) admin / member 생성
    admin_email = "admin_dues@example.com"
    member_email = "member_dues@example.com"
    pw = "TestPassword123!"

    _register(client, admin_email, pw, name="관리자", student_id="20262000")
    _register(client, member_email, pw, name="부원", student_id="20262001")

    # 2) DB에서 역할 부여
    _set_role(db, admin_email, Role.ADMIN)
    member = _set_role(db, member_email, Role.MEMBER)

    # 3) 로그인
    admin_token = _login(client, admin_email, pw)
    member_token = _login(client, member_email, pw)

    # 4) (관리자) 해당 월 회비 청구 생성
    r = client.post(
        "/admin/dues/charges",
        json={"period": PERIOD, "amount": 10000},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    charge = r.json()
    assert charge["period"] == PERIOD
    assert charge["amount"] == 10000

    # 5) (회원) 내 회비 상태 확인 -> UNPAID
    r = client.get("/dues/me", params={"period": PERIOD}, headers={"Authorization": f"Bearer {member_token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["current_period"] == PERIOD
    assert body["current_amount"] == 10000
    assert body["paid_amount"] == 0
    assert body["status"] == "UNPAID"

    # 6) (관리자) 납부 처리
    r = client.post(
        "/admin/dues/payments",
        json={
            "user_id": str(member.id),
            "period": PERIOD,
            "amount": 10000,
            "method": "TRANSFER",
            "memo": "테스트 납부",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    payment = r.json()
    assert payment["amount"] == 10000
    assert payment["method"] == "TRANSFER"

    # 7) (회원) 상태 확인 -> PAID
    r = client.get("/dues/me", params={"period": PERIOD}, headers={"Authorization": f"Bearer {member_token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["paid_amount"] == 10000
    assert body["status"] == "PAID"

    # 8) (관리자) 월별 납부 현황 -> PAID로 나와야 함
    r = client.get(
        "/admin/dues/status",
        params={"period": PERIOD},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    rows = r.json()
    # 최소 1명(부원)이 포함
    assert any(row["user_id"] == str(member.id) and row["status"] == "PAID" for row in rows)


def test_dues_partial_payment(client, db):
    admin_email = "admin_dues2@example.com"
    member_email = "member_dues2@example.com"
    pw = "TestPassword123!"
    period = "2026-02"

    _register(client, admin_email, pw, name="관리자2", student_id="20263000")
    _register(client, member_email, pw, name="부원2", student_id="20263001")

    _set_role(db, admin_email, Role.ADMIN)
    member = _set_role(db, member_email, Role.MEMBER)

    admin_token = _login(client, admin_email, pw)
    member_token = _login(client, member_email, pw)

    # 청구 10,000
    r = client.post(
        "/admin/dues/charges",
        json={"period": period, "amount": 10000},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text

    # 부분 납부 3,000
    r = client.post(
        "/admin/dues/payments",
        json={"user_id": str(member.id), "period": period, "amount": 3000, "method": "CASH"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text

    # MEMBER 상태: PARTIAL
    r = client.get("/dues/me", params={"period": period}, headers={"Authorization": f"Bearer {member_token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["paid_amount"] == 3000
    assert body["status"] == "PARTIAL"
