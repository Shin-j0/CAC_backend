"""





관리자 회비 현황 XLSX export 테스트.
- ADMIN 접근, period 검증, attachment 헤더,
  XLSX 응답 content-type 및 파일 시그니처(PK) 확인.



"""
from tests.helpers import auth_header, setup_admin_and_member


def test_admin_dues_export_xlsx_ok(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]

    period = "2026-10"
    amount = 10000

    # 청구 + 납부 (데이터 하나라도 들어가게)
    c = client.post(
        "/admin/dues/charges",
        headers=auth_header(admin_token),
        json={"period": period, "amount": amount},
    )
    assert c.status_code == 200, c.text

    p = client.post(
        "/admin/dues/payments",
        headers=auth_header(admin_token),
        json={"user_id": user_id, "period": period, "amount": 5000, "method": "TRANSFER", "memo": "부분"},
    )
    assert p.status_code == 200, p.text

    res = client.get(f"/admin/dues/export.xlsx?period={period}", headers=auth_header(admin_token))
    assert res.status_code == 200

    # content-type
    ct = res.headers.get("content-type", "")
    assert ct.startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # attachment
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert period in cd

    # XLSX는 ZIP 기반 포맷이라 앞부분이 PK로 시작
    assert res.content[:2] == b"PK"


def test_admin_dues_export_xlsx_invalid_period_400(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    res = client.get("/admin/dues/export.xlsx?period=2026-13", headers=auth_header(admin_token))
    assert res.status_code == 400
    assert res.json()["detail"] == "month must be between 01 and 12"
