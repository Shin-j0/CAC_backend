"""





관리자 회비 납부내역 CSV export 테스트.
- 특정 period 납부 기록 2건 생성 후 export 결과(헤더/행 수/금액),
  attachment 헤더 및 period 검증(400) 확인.



"""
import csv
import io
from tests.helpers import auth_header, setup_admin_and_member

def _parse_csv_text(text: str) -> list[list[str]]:
    text = text.lstrip("\ufeff")  # BOM 제거
    return list(csv.reader(io.StringIO(text)))

def test_admin_dues_payments_export_csv_ok(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]

    period = "2026-09"
    amount = 10000

    # 청구
    c = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": period, "amount": amount})
    assert c.status_code == 200, c.text

    # 납부 2건
    p1 = client.post("/admin/dues/payments", headers=auth_header(admin_token),
                     json={"user_id": user_id, "period": period, "amount": 4000, "method": "TRANSFER", "memo": "1차"})
    assert p1.status_code == 200, p1.text

    p2 = client.post("/admin/dues/payments", headers=auth_header(admin_token),
                     json={"user_id": user_id, "period": period, "amount": 6000, "method": "TRANSFER", "memo": "2차"})
    assert p2.status_code == 200, p2.text

    # export
    res = client.get(f"/admin/dues/payments/export?period={period}", headers=auth_header(admin_token))
    assert res.status_code == 200, res.text
    assert res.headers.get("content-type", "").startswith("text/csv")
    assert "attachment" in res.headers.get("content-disposition", "")

    rows = _parse_csv_text(res.text)
    assert rows[0] == ["period", "payment_id", "user_id", "amount", "method", "memo", "created_by", "created_at"]
    assert len(rows) == 3  # header + 2 rows

    amounts = sorted(int(r[3]) for r in rows[1:])
    assert amounts == [4000, 6000]

def test_admin_dues_payments_export_csv_invalid_period_400(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    res = client.get("/admin/dues/payments/export?period=2026-13", headers=auth_header(admin_token))
    assert res.status_code == 400
    assert res.json()["detail"] == "month must be between 01 and 12"
