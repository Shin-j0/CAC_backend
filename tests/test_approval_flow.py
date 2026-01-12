def test_guest_cannot_access_member_feature_until_approved(client):
    # 1) 회원가입(GUEST)
    email = "guest1@example.com"
    pw = "TestPassword123!"
    r = client.post("/auth/register", json={
        "email": email, "password": pw,
        "name": "게스트", "student_id": "20231111",
        "phone": "010-1111-1111", "grade": 1
    })
    assert r.status_code in (200, 201)

    # 2) 로그인
    r = client.post("/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200
    access = r.json()["access_token"]

    # 3) (예시) MEMBER 전용 엔드포인트 접근 시도 -> 403
    r = client.get("/members-only", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 403

    # 4) ADMIN이 승인 (테스트에서는 admin 계정 만들어 role=ADMIN으로 직접 세팅하거나 admin 승인 API 사용)
    # ... 여기 부분은 네 admin 생성 방식에 맞춰 내가 딱 맞게 작성해줄 수 있음
