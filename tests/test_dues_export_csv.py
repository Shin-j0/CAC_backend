"""





관리자 회비 현황 CSV export 테스트.
- ADMIN 접근, period 검증, CSV 헤더/데이터 행 포함,
  Content-Disposition(attachment) 및 BOM(utf-8-sig) 처리 확인.


"""

import csv
import io

from tests.helpers import auth_header, setup_admin_and_member


def _parse_csv_text(text: str) -> list[list[str]]:
    # Excel 호환을 위해 서버가 utf-8-sig(BOM)를 쓸 수 있으니 BOM 제거
    text = text.lstrip("\ufeff")
    f = io.StringIO(text)
    return list(csv.reader(f))


def test_admin_dues_export_csv_ok(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]
    student_id = ctx["user_student_id"]

    period = "2026-08"
    amount = 10000

    # 청구 생성
    r1 = client.post(
        "/admin/dues/charges",
        headers=auth_header(admin_token),
        json={"period": period, "amount": amount},
    )
    assert r1.status_code == 200, r1.text

    # 부분 납부 -> PARTIAL
    r2 = client.post(
        "/admin/dues/payments",
        headers=auth_header(admin_token),
        json={"user_id": user_id, "period": period, "amount": 7000, "method": "TRANSFER", "memo": "부분"},
    )
    assert r2.status_code == 200, r2.text

    # CSV export
    res = client.get(f"/admin/dues/export?period={period}", headers=auth_header(admin_token))
    assert res.status_code == 200, res.text
    assert res.headers.get("content-type", "").startswith("text/csv")
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert period in cd  # 파일명에 period 포함

    rows = _parse_csv_text(res.text)
    assert rows[0] == ["period", "name", "student_id", "status", "amount_due", "paid_amount"]

    # user row 찾기
    data_rows = rows[1:]
    assert len(data_rows) >= 1
    row = next((r for r in data_rows if len(r) >= 6 and r[2] == student_id), None)
    assert row is not None, f"CSV missing row for student_id={student_id}: {data_rows}"
    assert row[0] == period
    assert row[3] == "PARTIAL"
    assert row[4] == str(amount)
    assert row[5] == "7000"


def test_admin_dues_export_csv_invalid_period_400(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    res = client.get("/admin/dues/export?period=2026-13", headers=auth_header(admin_token))
    assert res.status_code == 400
    assert res.json()["detail"] == "month must be between 01 and 12"
