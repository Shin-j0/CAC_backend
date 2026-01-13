from sqlalchemy import select
from app.models.user import User, Role


def test_guest_approval_flow_end_to_end(client, db):
    """기존 test_approval_flow.py가 'members-only' 같은 예시 엔드포인트를 가정해서,
    실제 API(guest 승인) 기준으로 end-to-end 흐름을 검증합니다.
    """
    guest_email = "guest_approve@example.com"
    pw = "TestPassword123!"

    # 1) GUEST 회원가입
    r = client.post("/auth/register", json={
        "email": guest_email, "password": pw,
        "name": "게스트", "student_id": "20264000",
        "phone": "010-1111-1111", "grade": 1
    })
    assert r.status_code in (200, 201), r.text

    # 2) 관리자 계정 생성 후 ADMIN으로 승격
    admin_email = "admin_approve@example.com"
    r = client.post("/auth/register", json={
        "email": admin_email, "password": pw,
        "name": "관리자", "student_id": "20264001",
        "phone": "010-2222-2222", "grade": 1
    })
    assert r.status_code in (200, 201), r.text

    admin = db.scalar(select(User).where(User.email == admin_email))
    assert admin is not None
    admin.role = Role.ADMIN
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # 3) 관리자 로그인
    r = client.post("/auth/login", json={"email": admin_email, "password": pw})
    assert r.status_code == 200, r.text
    admin_token = r.json()["access_token"]

    # 4) 대기자 목록에 guest가 포함되는지
    r = client.get("/admin/pending-users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text
    pending = r.json()
    assert any(p["email"] == guest_email for p in pending)

    guest = db.scalar(select(User).where(User.email == guest_email))
    assert guest is not None

    # 5) 승인
    r = client.post(f"/admin/guest/{guest.id}/approve", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text

    db.refresh(guest)
    assert guest.role == Role.MEMBER
