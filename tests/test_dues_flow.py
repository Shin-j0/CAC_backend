"""



회비 도메인(청구/납부/상태) 통합 테스트.
- PAID/PARTIAL/UNPAID 상태 계산, 누적 미납(arrears_total) 합산,
  중복 청구 방지 및 period 형식/월 범위 검증,
  관리자 월별 현황(/admin/dues/status) 결과까지 확인한다.



"""


from tests.helpers import auth_header, setup_admin_and_member


def _find_status_row(rows: list[dict], user_id: str) -> dict:
    row = next((r for r in rows if r.get("user_id") == user_id), None)
    assert row is not None, f"status rows missing user_id={user_id}"
    return row


def test_dues_paid_status_with_admin_status(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]
    user_token = ctx["user_token"]
    student_id = ctx["user_student_id"]

    period = "2026-02"
    charge_amount = 10000

    # 청구 생성
    charge = client.post(
        "/admin/dues/charges",
        headers=auth_header(admin_token),
        json={"period": period, "amount": charge_amount},
    )
    assert charge.status_code == 200, charge.text

    # 완납
    pay = client.post(
        "/admin/dues/payments",
        headers=auth_header(admin_token),
        json={"user_id": user_id, "period": period, "amount": charge_amount, "method": "TRANSFER", "memo": "완납"},
    )
    assert pay.status_code == 200, pay.text

    # MEMBER: 내 상태
    my_status = client.get(f"/dues/me?period={period}", headers=auth_header(user_token))
    assert my_status.status_code == 200, my_status.text
    body = my_status.json()["data"]
    assert body["status"] == "PAID"
    assert body["paid_amount"] == charge_amount
    assert body["arrears_total"] == 0

    # ADMIN: 월별 현황
    status = client.get(f"/admin/dues/status?period={period}", headers=auth_header(admin_token))
    assert status.status_code == 200, status.text
    rows = status.json()["data"]
    assert len(rows) == status.json()["meta"]["count"]
    row = _find_status_row(rows, user_id)
    assert row["student_id"] == student_id
    assert row["amount_due"] == charge_amount
    assert row["paid_amount"] == charge_amount
    assert row["status"] == "PAID"


def test_dues_partial_status_with_admin_status(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]
    user_token = ctx["user_token"]
    student_id = ctx["user_student_id"]

    period = "2026-03"
    charge_amount = 10000
    paid_amount = 7000

    # 청구 생성
    charge = client.post(
        "/admin/dues/charges",
        headers=auth_header(admin_token),
        json={"period": period, "amount": charge_amount},
    )
    assert charge.status_code == 200, charge.text

    # 부분 납부
    pay = client.post(
        "/admin/dues/payments",
        headers=auth_header(admin_token),
        json={"user_id": user_id, "period": period, "amount": paid_amount, "method": "TRANSFER", "memo": "부분 납부"},
    )
    assert pay.status_code == 200, pay.text

    # MEMBER: 내 상태 -> PARTIAL
    my_status = client.get(f"/dues/me?period={period}", headers=auth_header(user_token))
    assert my_status.status_code == 200, my_status.text
    body = my_status.json()["data"]
    assert body["current_period"] == period
    assert body["current_amount"] == charge_amount
    assert body["paid_amount"] == paid_amount
    assert body["status"] == "PARTIAL"
    assert body["arrears_total"] == (charge_amount - paid_amount)

    # ADMIN: 월별 현황 -> PARTIAL
    status = client.get(f"/admin/dues/status?period={period}", headers=auth_header(admin_token))
    assert status.status_code == 200, status.text
    rows = status.json()["data"]
    assert len(rows) == status.json()["meta"]["count"]
    row = _find_status_row(rows, user_id)
    assert row["student_id"] == student_id
    assert row["amount_due"] == charge_amount
    assert row["paid_amount"] == paid_amount
    assert row["status"] == "PARTIAL"


def test_dues_unpaid_status_with_admin_status(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]
    user_token = ctx["user_token"]
    student_id = ctx["user_student_id"]

    period = "2026-04"
    charge_amount = 10000

    # 청구만 생성 (납부 없음)
    charge = client.post(
        "/admin/dues/charges",
        headers=auth_header(admin_token),
        json={"period": period, "amount": charge_amount},
    )
    assert charge.status_code == 200, charge.text

    # MEMBER: 내 상태 -> UNPAID
    my_status = client.get(f"/dues/me?period={period}", headers=auth_header(user_token))
    assert my_status.status_code == 200, my_status.text
    body = my_status.json()["data"]
    assert body["status"] == "UNPAID"
    assert body["paid_amount"] == 0
    assert body["arrears_total"] == charge_amount

    # ADMIN: 월별 현황 -> UNPAID
    status = client.get(f"/admin/dues/status?period={period}", headers=auth_header(admin_token))
    assert status.status_code == 200, status.text
    rows = status.json()["data"]
    assert len(rows) == status.json()["meta"]["count"]
    row = _find_status_row(rows, user_id)
    assert row["student_id"] == student_id
    assert row["amount_due"] == charge_amount
    assert row["paid_amount"] == 0
    assert row["status"] == "UNPAID"


def test_dues_arrears_total_accumulates_across_periods_with_admin_status(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]
    user_id = ctx["user_id"]
    user_token = ctx["user_token"]

    p1 = "2026-05"
    p2 = "2026-06"
    amount = 10000

    # 청구 2개 생성
    r1 = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": p1, "amount": amount})
    assert r1.status_code == 200, r1.text

    r2 = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": p2, "amount": amount})
    assert r2.status_code == 200, r2.text

    # 첫 달만 완납
    pay1 = client.post(
        "/admin/dues/payments",
        headers=auth_header(admin_token),
        json={"user_id": user_id, "period": p1, "amount": amount, "method": "TRANSFER", "memo": "5월 완납"},
    )
    assert pay1.status_code == 200, pay1.text

    # 둘째 달 기준 조회:
    # - p2는 미납이므로 UNPAID
    # - arrears_total은 p1 완납(0) + p2 미납(10000) = 10000
    my_status = client.get(f"/dues/me?period={p2}", headers=auth_header(user_token))
    assert my_status.status_code == 200, my_status.text
    body = my_status.json()["data"]
    assert body["current_period"] == p2
    assert body["status"] == "UNPAID"
    assert body["arrears_total"] == amount

    # ADMIN 월별 현황은 period별 테이블이므로:
    # p1 -> PAID / p2 -> UNPAID 를 각각 조회해서 확인
    s1 = client.get(f"/admin/dues/status?period={p1}", headers=auth_header(admin_token))
    assert s1.status_code == 200, s1.text
    s1_data = s1.json()["data"]
    assert len(s1_data) == s1.json()["meta"]["count"]
    row1 = _find_status_row(s1_data, user_id)
    assert row1["status"] == "PAID"
    assert row1["paid_amount"] == amount
    assert row1["amount_due"] == amount

    s2 = client.get(f"/admin/dues/status?period={p2}", headers=auth_header(admin_token))
    assert s2.status_code == 200, s2.text
    s2_data = s2.json()["data"]
    assert len(s2_data) == s2.json()["meta"]["count"]
    row2 = _find_status_row(s2_data, user_id)
    assert row2["status"] == "UNPAID"
    assert row2["paid_amount"] == 0
    assert row2["amount_due"] == amount


def test_dues_charge_duplicate_period_rejected(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    period = "2026-07"
    amount = 10000

    r1 = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": period, "amount": amount})
    assert r1.status_code == 200, r1.text

    r2 = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": period, "amount": amount})
    assert r2.status_code == 400, r2.text
    assert r2.json()["detail"] == "charge for that period already exists"


def test_dues_charge_invalid_period_format_rejected(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    bad_period = "2026-7"  # ❌ 2026-07 != 2026-7  월 2자리

    r = client.post("/admin/dues/charges", headers=auth_header(admin_token), json={"period": bad_period, "amount": 10000})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "period must be in 'YYYY-MM' format"


# 2026-00 or 2026-13 1월~12월 오류 체크
def test_dues_charge_invalid_month_range_rejected(client, db_session):
    ctx = setup_admin_and_member(client, db_session)
    admin_token = ctx["admin_token"]

    for bad_period in ["2026-00", "2026-13"]:
        r = client.post(
            "/admin/dues/charges",
            headers=auth_header(admin_token),
            json={"period": bad_period, "amount": 10000},
        )
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "month must be between 01 and 12"
