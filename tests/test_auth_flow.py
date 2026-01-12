def test_register_login_me(client):
    email = "testuser@example.com"
    password = "TestPassword123!"
    payload = {
        "email": email,
        "password": password,
        "name": "테스트유저",
        "student_id": "20230000",
        "phone": "010-0000-0000",
        "grade": 1
    }

    # 1) 회원가입
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text

    # 2) 로그인
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    token = data["access_token"]

    # 3) 내 정보 조회
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["email"] == email

def test_refresh_flow(client):
    email = "refresh@example.com"
    pw = "TestPassword123!"
    client.post("/auth/register", json={
        "email": email, "password": pw, "name": "리프레시", "student_id": "20239999", "phone": "010-0000-0000", "grade": 1
    })
    r = client.post("/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200
    assert "access_token" in r.json()

    # refresh는 쿠키 기반이라 Authorization 없어도 됨
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    assert "access_token" in r.json()

    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json()["ok"] is True
